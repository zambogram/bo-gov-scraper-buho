#!/bin/bash
#
# Script para scraping histórico completo de todos los sitios
# BO-GOV-SCRAPER-BUHO
#
# Uso:
#   chmod +x scripts/scrape_historico_completo.sh
#   ./scripts/scrape_historico_completo.sh
#

# Configuración
LIMITE=100  # Límite de documentos por sitio en cada corrida
MODO="full"  # full = histórico completo, delta = solo nuevos
MAX_RETRIES=3  # Número máximo de reintentos por sitio

# Lista de sitios a procesar
SITIOS=(
  "tcp"
  "tsj"
  "asfi"
  "sin"
  "contraloria"
  # Agregar más sitios aquí según se vayan configurando
  # "gaceta_oficial"
  # "ministerio_trabajo"
  # "tribunal_agroambiental"
  # ... hasta 30+ sitios
)

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para ejecutar con reintentos
run_with_retry() {
  local sitio=$1
  local retries=0
  local success=false

  while [ $retries -lt $MAX_RETRIES ] && [ "$success" = false ]; do
    if [ $retries -gt 0 ]; then
      local wait_time=$((2 ** retries))  # Exponential backoff: 2, 4, 8 segundos
      echo -e "${YELLOW}  Reintento $retries/$MAX_RETRIES después de ${wait_time}s...${NC}"
      sleep $wait_time
    fi

    # Ejecutar scraping con logging
    if timeout 600 python main.py scrape "$sitio" --mode "$MODO" --limit "$LIMITE" --save-txt --save-json 2>&1 | tee -a "logs/historico_${sitio}_$(date '+%Y%m%d').log"; then
      success=true
      echo -e "${GREEN}✓ $sitio completado exitosamente${NC}"
      return 0
    else
      retries=$((retries + 1))
      if [ $retries -lt $MAX_RETRIES ]; then
        echo -e "${YELLOW}⚠ Error en $sitio (intento $retries/$MAX_RETRIES), reintentando...${NC}"
      fi
    fi
  done

  if [ "$success" = false ]; then
    echo -e "${RED}✗ Error en $sitio después de $MAX_RETRIES intentos${NC}"
    # Guardar sitio fallido para revisión manual
    echo "$sitio" >> "logs/sitios_fallidos_$(date '+%Y%m%d').txt"
    return 1
  fi
}

# Crear directorio de logs si no existe
mkdir -p logs

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  BÚHO - Scraping Histórico Completo${NC}"
echo -e "${BLUE}  Procesando ${#SITIOS[@]} sitios${NC}"
echo -e "${BLUE}  Máximo $MAX_RETRIES reintentos por sitio${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Timestamp de inicio
START_TIME=$(date +%s)
TOTAL_SITIOS=${#SITIOS[@]}
SITIOS_EXITOSOS=0
SITIOS_FALLIDOS=0

# Procesar cada sitio
for i in "${!SITIOS[@]}"; do
  sitio="${SITIOS[$i]}"
  num=$((i+1))

  echo ""
  echo -e "${BLUE}====================================== [$num/$TOTAL_SITIOS]${NC}"
  echo -e "${GREEN}Procesando: $sitio${NC}"
  echo -e "${BLUE}======================================${NC}"

  # Ejecutar con reintentos y timeout
  if run_with_retry "$sitio"; then
    SITIOS_EXITOSOS=$((SITIOS_EXITOSOS+1))
  else
    SITIOS_FALLIDOS=$((SITIOS_FALLIDOS+1))
  fi

  # Pausa entre sitios para no sobrecargar (solo si no es el último)
  if [ $num -lt $TOTAL_SITIOS ]; then
    echo ""
    echo "Pausando 30 segundos antes del siguiente sitio..."
    sleep 30
  fi
done

# Timestamp final
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}  Scraping Histórico Completado${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}Sitios procesados exitosamente: $SITIOS_EXITOSOS${NC}"
echo -e "${RED}Sitios con errores: $SITIOS_FALLIDOS${NC}"
echo -e "${BLUE}Duración total: ${MINUTES}m ${SECONDS}s${NC}"
echo ""

# Advertir sobre sitios fallidos
if [ $SITIOS_FALLIDOS -gt 0 ]; then
  echo -e "${YELLOW}⚠ Sitios con errores guardados en: logs/sitios_fallidos_$(date '+%Y%m%d').txt${NC}"
  echo ""
fi

# Mostrar estadísticas finales
echo -e "${BLUE}Generando estadísticas globales...${NC}"
python main.py stats

echo ""
echo -e "${GREEN}Proceso completado.${NC}"
echo -e "${BLUE}Ver archivos en:${NC}"
echo "  - Datos normalizados: data/normalized/"
echo "  - Exportaciones: exports/"
echo "  - Tracking: data/tracking_historico.json"
echo "  - Logs: logs/"
echo ""
