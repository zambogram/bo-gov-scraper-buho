#!/bin/bash
#
# Script para delta updates diarios (solo nuevos documentos)
# BO-GOV-SCRAPER-BUHO
#
# Configurar en cron para ejecución automática:
#   crontab -e
#   0 2 * * * /ruta/a/scripts/scrape_delta_daily.sh >> /var/log/buho_delta.log 2>&1
#

# Configuración
LIMITE=50  # Límite de nuevos documentos a buscar por sitio
MODO="delta"  # Delta = solo nuevos
MAX_RETRIES=3  # Número máximo de reintentos por sitio

# Lista de sitios activos
SITIOS=(
  "tcp"
  "tsj"
  "asfi"
  "sin"
  "contraloria"
  # Agregar más sitios según configuración
)

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

    # Ejecutar delta update
    if python main.py scrape "$sitio" --mode "$MODO" --limit "$LIMITE" --save-txt --save-json 2>&1 | tee -a "logs/delta_${sitio}_$(date '+%Y%m%d').log"; then
      success=true
      echo -e "${GREEN}✓ $sitio actualizado exitosamente${NC}"
      return 0
    else
      retries=$((retries + 1))
      if [ $retries -lt $MAX_RETRIES ]; then
        echo -e "${YELLOW}⚠ Error en $sitio, reintentando...${NC}"
      fi
    fi
  done

  if [ "$success" = false ]; then
    echo -e "${RED}✗ Error en $sitio después de $MAX_RETRIES intentos${NC}"
    return 1
  fi
}

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  BÚHO - Delta Update Diario${NC}"
echo -e "${BLUE}  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

TOTAL_NUEVOS=0
SITIOS_EXITOSOS=0
SITIOS_FALLIDOS=0

for sitio in "${SITIOS[@]}"; do
  echo ""
  echo -e "${BLUE}Actualizando: $sitio${NC}"

  # Ejecutar con reintentos
  if run_with_retry "$sitio"; then
    SITIOS_EXITOSOS=$((SITIOS_EXITOSOS + 1))
  else
    SITIOS_FALLIDOS=$((SITIOS_FALLIDOS + 1))
  fi

  # Pausa breve entre sitios
  sleep 10
done

echo ""
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}  Delta Update Completado${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}Sitios exitosos: $SITIOS_EXITOSOS${NC}"
echo -e "${RED}Sitios fallidos: $SITIOS_FALLIDOS${NC}"
echo ""

# Mostrar estadísticas
python main.py stats

echo ""
echo -e "${GREEN}Delta update finalizado: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
