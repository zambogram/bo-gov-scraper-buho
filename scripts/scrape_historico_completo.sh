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
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  BÚHO - Scraping Histórico Completo${NC}"
echo -e "${BLUE}  Procesando ${#SITIOS[@]} sitios${NC}"
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

  # Ejecutar scraping
  python main.py scrape "$sitio" --mode "$MODO" --limit "$LIMITE" --save-txt --save-json

  # Verificar resultado
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ $sitio completado exitosamente${NC}"
    SITIOS_EXITOSOS=$((SITIOS_EXITOSOS+1))
  else
    echo -e "${RED}✗ Error procesando $sitio${NC}"
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

# Mostrar estadísticas finales
echo -e "${BLUE}Generando estadísticas globales...${NC}"
python main.py stats

echo ""
echo -e "${GREEN}Proceso completado.${NC}"
echo -e "${BLUE}Ver archivos en:${NC}"
echo "  - Datos normalizados: data/normalized/"
echo "  - Exportaciones: exports/"
echo "  - Tracking: data/tracking_historico.json"
echo ""
