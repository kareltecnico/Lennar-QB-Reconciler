# Lennar-QB Reconciler v1.0 📊

Un motor de auditoría profesional diseñado para cruzar la facturación nativa de **Lennar** contra los registros de **QuickBooks**, identificando errores contables al centavo a través de un algoritmo inteligente de Compensación de Fases.

## 🛠 Instalación Rápida

La herramienta está construida en Python puro (Multiplataforma Mac/Windows).

1. Ingresa a la carpeta del proyecto.
2. Genera y activa tu entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Mac/Linux
   # venv\\Scripts\\activate   # En Windows
   ```
3. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

## 🧠 Algoritmo de Compensación de Fases

Durante el ciclo de conciliación de pagos de obra, es habitual que la constructora (Lennar) asigne un pago a una Fase específica (ej. `Final` o `Phase C`), mientras que administrativamente se ingresa en QuickBooks bajo una fase distinta para forzar la cuadratura de caja registradora (ej. `Extras` o `Phase X`).

El **Lennar-QB Reconciler** soluciona esto aislando falsos positivos con una estrategia robusta en dos pasos:

1. **Agrupación Macro:** Calcula primero el `Net_Diff` (Diferencia Neta) agrupando absolutamente todos los pagos del mismo *Proyecto Normalizado*, ignorando a qué fase pertenecen temporalmente.
2. **Compensación Condicional:** 
   - Si la suma total de cobros vs pagos del proyecto da `$0.00`, la herramienta asume que existieron **Diferencias Compensadas** y marca el proyecto completo como `✅ PROYECTO OK`.
   - Si existe una variación neta distinta de cero, entra a la **Fase Analítica**, buscando cruzar `Phase` contra `Phase` para identificar exactamente la línea problemática, imprimiendo un dictamen `🔴 ERROR DETECTADO` junto con el nombre del proyecto, el Memo de QuickBooks causante y la acción correctiva.

## 📈 Visualizador: Dashboard Pro (HTML)

El sistema genera ahora automáticamente una salida web moderna (con Dark Theme y Bootstrap 5) para los líderes de facturación e ingenieros.

Al correr la herramienta una vez, los resultados se guardarán automáticamente en una carpeta protegida `.gitignore` llamada `output/`

📍 Para abrir el resultado visual:
*Abre en cualquier navegador el archivo generado `output/dashboard.html`*

## ▶ Ejecución

Para iniciar la conciliación y generar simultáneamente en un solo comando el CSV, el log en Markdown, el Dashboard HTML y la respuesta por consola usa:

```bash
python src/reconciler.py
```

## 🚀 Roadmap
- **Versión 2.0 - Módulo de Interacción**: Interfaz visual directa para la carga selectiva de plantillas de archivos de Lennar y QuickBooks en lugar de lectura de rutas estáticas, junto a un generador automático de correos para contratistas.
