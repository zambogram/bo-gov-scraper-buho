"""
Modelos de datos para documentos legales y artículos
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import hashlib
import json


@dataclass
class Articulo:
    """Modelo para un artículo o sección dentro de un documento legal"""
    id_articulo: str
    id_documento: str
    numero: Optional[str] = None  # "Artículo 1", "Art. 5", "Sección I"
    titulo: Optional[str] = None
    contenido: str = ""
    tipo_unidad: str = "articulo"  # articulo, seccion, capitulo, titulo, disposicion
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Articulo':
        """Crear desde diccionario"""
        return cls(**data)


@dataclass
class Documento:
    """Modelo para un documento legal (ley, sentencia, resolución, etc.)"""
    id_documento: str
    site: str  # tcp, tsj, asfi, sin, contraloria, gaceta_oficial
    tipo_documento: str  # Ley, Decreto Supremo, Sentencia, etc.
    numero_norma: Optional[str] = None
    fecha: Optional[str] = None  # ISO format YYYY-MM-DD
    fecha_publicacion: Optional[str] = None
    titulo: Optional[str] = None
    sumilla: Optional[str] = None
    url_origen: Optional[str] = None

    # Rutas de archivos
    ruta_pdf: Optional[str] = None
    ruta_txt: Optional[str] = None
    ruta_json: Optional[str] = None

    # Contenido
    texto_completo: str = ""
    articulos: List[Articulo] = field(default_factory=list)

    # Metadata adicional
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Control de versiones
    hash_contenido: Optional[str] = None
    fecha_scraping: Optional[str] = None
    fecha_ultima_actualizacion: Optional[str] = None

    def __post_init__(self):
        """Generar ID y hash si no existen"""
        if not self.id_documento:
            self.id_documento = self._generar_id()

        if not self.fecha_scraping:
            self.fecha_scraping = datetime.now().isoformat()

    def _generar_id(self) -> str:
        """Generar ID único basado en site, tipo y número"""
        base = f"{self.site}_{self.tipo_documento}_{self.numero_norma}_{self.fecha}"
        return hashlib.md5(base.encode()).hexdigest()[:16]

    def calcular_hash(self) -> str:
        """Calcular hash MD5 del contenido para detectar cambios"""
        content = f"{self.texto_completo}{len(self.articulos)}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def actualizar_hash(self) -> None:
        """Actualizar hash del contenido"""
        self.hash_contenido = self.calcular_hash()
        self.fecha_ultima_actualizacion = datetime.now().isoformat()

    def agregar_articulo(self, articulo: Articulo) -> None:
        """Agregar un artículo al documento"""
        self.articulos.append(articulo)

    def to_dict(self, incluir_articulos: bool = True) -> Dict[str, Any]:
        """
        Convertir a diccionario

        Args:
            incluir_articulos: Si incluir la lista completa de artículos
        """
        data = {
            'id_documento': self.id_documento,
            'site': self.site,
            'tipo_documento': self.tipo_documento,
            'numero_norma': self.numero_norma,
            'fecha': self.fecha,
            'fecha_publicacion': self.fecha_publicacion,
            'titulo': self.titulo,
            'sumilla': self.sumilla,
            'url_origen': self.url_origen,
            'ruta_pdf': self.ruta_pdf,
            'ruta_txt': self.ruta_txt,
            'ruta_json': self.ruta_json,
            'texto_completo': self.texto_completo,
            'metadata': self.metadata,
            'hash_contenido': self.hash_contenido,
            'fecha_scraping': self.fecha_scraping,
            'fecha_ultima_actualizacion': self.fecha_ultima_actualizacion,
        }

        if incluir_articulos:
            data['articulos'] = [art.to_dict() for art in self.articulos]
        else:
            data['total_articulos'] = len(self.articulos)

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Documento':
        """Crear documento desde diccionario"""
        # Extraer artículos si existen
        articulos_data = data.pop('articulos', [])
        articulos = [Articulo.from_dict(art) for art in articulos_data]

        # Crear documento
        doc = cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
        doc.articulos = articulos

        return doc

    def guardar_json(self, ruta: Optional[Path] = None) -> Path:
        """
        Guardar documento como JSON

        Args:
            ruta: Ruta donde guardar, si None usa ruta_json

        Returns:
            Path del archivo guardado
        """
        if ruta is None:
            if not self.ruta_json:
                raise ValueError("No se especificó ruta para guardar JSON")
            ruta = Path(self.ruta_json)

        # Asegurar que el directorio existe
        ruta.parent.mkdir(parents=True, exist_ok=True)

        # Guardar
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

        return ruta

    @classmethod
    def cargar_json(cls, ruta: Path) -> 'Documento':
        """
        Cargar documento desde JSON

        Args:
            ruta: Path del archivo JSON

        Returns:
            Documento cargado
        """
        with open(ruta, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return cls.from_dict(data)


@dataclass
class PipelineResult:
    """Resultado de ejecutar el pipeline de scraping"""
    site_id: str
    modo: str  # "full" o "delta"
    inicio: datetime = field(default_factory=datetime.now)
    fin: Optional[datetime] = None

    # Contadores
    total_encontrados: int = 0
    total_nuevos: int = 0
    total_actualizados: int = 0
    total_descargados: int = 0
    total_parseados: int = 0
    total_errores: int = 0

    # Listas de resultados
    documentos_procesados: List[str] = field(default_factory=list)
    errores: List[Dict[str, str]] = field(default_factory=list)

    # Mensajes de progreso
    mensajes: List[str] = field(default_factory=list)

    def agregar_mensaje(self, mensaje: str) -> None:
        """Agregar mensaje de progreso"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.mensajes.append(f"[{timestamp}] {mensaje}")

    def agregar_error(self, descripcion: str, detalle: str = "") -> None:
        """Agregar error"""
        self.total_errores += 1
        self.errores.append({
            'timestamp': datetime.now().isoformat(),
            'descripcion': descripcion,
            'detalle': detalle
        })

    def finalizar(self) -> None:
        """Marcar como finalizado"""
        self.fin = datetime.now()

    @property
    def duracion_segundos(self) -> Optional[float]:
        """Duración en segundos"""
        if self.fin:
            return (self.fin - self.inicio).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'site_id': self.site_id,
            'modo': self.modo,
            'inicio': self.inicio.isoformat(),
            'fin': self.fin.isoformat() if self.fin else None,
            'duracion_segundos': self.duracion_segundos,
            'total_encontrados': self.total_encontrados,
            'total_nuevos': self.total_nuevos,
            'total_actualizados': self.total_actualizados,
            'total_descargados': self.total_descargados,
            'total_parseados': self.total_parseados,
            'total_errores': self.total_errores,
            'documentos_procesados': self.documentos_procesados,
            'errores': self.errores,
            'mensajes': self.mensajes[-50:]  # Solo últimos 50 mensajes
        }
