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
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  BÚHO - Delta Update Diario${NC}"
echo -e "${BLUE}  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

TOTAL_NUEVOS=0

for sitio in "${SITIOS[@]}"; do
  echo ""
  echo -e "${GREEN}Actualizando: $sitio${NC}"

  # Ejecutar delta update
  python main.py scrape "$sitio" --mode "$MODO" --limit "$LIMITE" --save-txt --save-json

  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ $sitio actualizado${NC}"
  else
    echo -e "✗ Error en $sitio"
  fi

  # Pausa breve entre sitios
  sleep 10
done

echo ""
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}  Delta Update Completado${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# Mostrar estadísticas
python main.py stats

echo ""
echo -e "${GREEN}Delta update finalizado: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
