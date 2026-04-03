# Lennar-QB Reconciler v2.0 📊

Un poderoso motor de auditoría profesional diseñado como Web App (Streamlit) interactiva para cruzar la facturación nativa de **Lennar** contra los registros de **QuickBooks**, identificando errores contables al centavo a través de un algoritmo inteligente de *Compensación de Fases*.

## 🛠 Instalación Rápida

La herramienta está construida en Python (Multiplataforma Mac/Windows).

1. Ingresa a la carpeta del proyecto.
2. Genera y activa tu entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Mac/Linux
   # venv\Scripts\activate   # En Windows
   ```
3. Instala las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Despliegue de la Web App

Para levantar la interfaz gráfica en modo local, solo debes dar un click en los accesos directos o correr el comando manualmente: 

**Directamente en la consola:**
```bash
streamlit run src/app.py
```

**Accesos Automáticos:**
- 🖥️ **Mac/Linux:** Escribe `sh run_app.sh` en tu terminal o dale doble click al archivo ejecutable local.
- 🪟 **Windows:** Dale enter/doble-click al archivo `run_app.bat`.

Automáticamente se abrirá una ventana en tu navegador por defecto `http://localhost:8501`.

## 🔋 Funciones de Dual Mode (Automático/Manual)
La Web App puede alimentarse de dos maneras:
1. **Puesta Automática:** Si agregas tus Excels con nombres fijos (`lennar check.xlsx`, `to check from qb.xlsx`, y `Mapeo de Nombres.xlsx`) dentro de la carpeta `/data/`, la aplicación correrá la auditoría la próxima vez que ingreses.
2. **Subida en vivo (Sidebar):** Usa la barra lateral de la Web App para subir los Excels directamente de tu sistema de archivos. Al subirlos, se guardarán y sobrescribirán en la carpeta `/data` para futuras consultas.

## 🧠 Algoritmo de Compensación de Fases

Durante el ciclo de conciliación de pagos de obra, es habitual que la constructora asigne un pago a una Fase específica `C`, mientras que administrativamente se ingresa en QuickBooks bajo una fase distinta `X`.

El **Lennar-QB Reconciler** aísla falsos positivos con una estrategia de dos pasos:
1. **Agrupación Macro:** Calcula primero el `Net_Diff` (Diferencia Neta) agrupando absolutamente todos los pagos del mismo *Proyecto Normalizado*, ignorando temporalmente la fase.
2. **Compensación Condicional:** 
   - Si la suma total de cobros vs pagos del proyecto da `$0.00`, la herramienta asume que existieron **Diferencias Compensadas** y lo lista oculto en un *Expander* de proyectos OK.
   - Si existe una variación neta distinta de cero, entra a la **Fase Analítica**. Muestra Tarjetas Rojas con el componente desfasado, el Subtotal de diferencias, Sub-Componentes Exactos y propone la *Acción Correctiva Exacta* en un Memo específico de QuickBooks.

## 📈 Roadmap
- **Versión 3.0:** Módulo de validación multi-cuenta en nube de QuickBooks Online.
