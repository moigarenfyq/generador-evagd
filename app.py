import streamlit as st
import streamlit.components.v1 as components
import requests
import pypdf

# Usamos el modelo estándar
MODELO = "gemini-1.5-flash"

st.set_page_config(
    page_title="Generador de Recursos EVAGD", page_icon="🏫", layout="centered"
)

st.title("🏫 Generador de Recursos para EVAGD (Canarias)")
st.markdown("""
Transforma tus apuntes en PDF en recursos listos para importar directamente en Moodle/EVAGD, 
alineados (opcionalmente) con tus Situaciones de Aprendizaje.
""")

st.caption(f"🤖 Modelo activo mediante conexión directa: `{MODELO}`")

st.divider()

# --- FORMULARIO DE CONFIGURACIÓN ---
MATERIAS = [
    "── ESO ──────────────────────────",
    "Biología y Geología",
    "Cultura Clásica",
    "Digitalización",
    "Economía y Emprendimiento",
    "Educación Física",
    "Educación Plástica, Visual y Audiovisual",
    "Física y Química",
    "Geografía e Historia",
    "Historia y Geografía de Canarias",
    "Inglés (Primera Lengua Extranjera)",
    "Latín",
    "Lengua Castellana y Literatura",
    "Matemáticas",
    "Música",
    "Religión",
    "Segunda Lengua Extranjera (Francés)",
    "Tecnología y Digitalización",
    "Valores Cívicos y Éticos",
    "── BACHILLERATO ─────────────────",
    "Anatomía Aplicada",
    "Análisis Musical I / II",
    "Artes Escénicas y Danza",
    "Biología",
    "Ciencias de la Tierra y del Medio Ambiente",
    "Cultura Audiovisual",
    "Cultura Científica",
    "Dibujo Técnico I / II",
    "Diseño",
    "Economía",
    "Economía de la Empresa",
    "Educación Física (1º Bach)",
    "Filosofía",
    "Física",
    "Geografía",
    "Griego I / II",
    "Historia de España",
    "Historia del Arte",
    "Historia del Mundo Contemporáneo",
    "Inglés",
    "Latín I / II",
    "Lenguaje y Práctica Musical",
    "Lengua Castellana y Literatura I / II",
    "Literatura Universal",
    "Matemáticas I / II (Ciencias)",
    "Matemáticas Aplicadas a las Ciencias Sociales I / II",
    "Matemáticas Generales",
    "Psicología",
    "Química",
    "Religión",
    "Segunda Lengua Extranjera (Francés)",
    "Tecnología e Ingeniería I / II",
]

CURSOS = [
    "1º ESO",
    "2º ESO",
    "3º ESO",
    "4º ESO",
    "1º Bachillerato",
    "2º Bachillerato",
]

st.subheader("1. Datos de la Asignatura")
col1, col2 = st.columns(2)
with col1:
    materia_sel = st.selectbox("Materia / Asignatura", MATERIAS, index=1)
    materia = materia_sel if not materia_sel.startswith("──") else ""
with col2:
    nivel = st.selectbox("Nivel / Curso", CURSOS, index=0)

st.divider()

st.subheader("2. Archivos Didácticos")
uploaded_apuntes = st.file_uploader(
    "Sube los Apuntes en PDF (Obligatorio)", type=["pdf"]
)
uploaded_sa = st.file_uploader(
    "Sube el PDF de la Situación de Aprendizaje (Opcional)", type=["pdf"]
)

st.divider()

st.subheader("3. Idioma de salida")
idioma = st.selectbox(
    "Idioma en el que se generará el recurso (para programas AICLE/bilingüe)",
    ["Español", "English", "Français"],
    index=0,
)

st.divider()

st.subheader("4. Formato de Destino en EVAGD")
tipo_recurso = st.radio(
    "¿Qué tipo de recurso quieres crear en EVAGD?",
    [
        "Libro (Archivo HTML único)",
        "Lección (Archivo Moodle XML)",
        "Cuestionario (Formato GIFT)",
    ],
    index=0,
)

st.divider()

# --- LÓGICA DE GENERACIÓN ---
if st.button("🚀 Generar Recurso Educativo", type="primary"):
    if not materia or not nivel:
        st.error("Por favor, rellena la materia y el nivel antes de continuar.")
    elif not uploaded_apuntes:
        st.error("Es obligatorio subir un archivo de apuntes en PDF.")
    else:
        with st.spinner(
            f"**{MODELO}** está procesando los documentos mediante pasarela directa v1..."
        ):
            try:
                # Comprobamos los Secrets de Streamlit
                if "GEMINI_API_KEY" not in st.secrets:
                    st.error("No se encontró la clave `GEMINI_API_KEY` en las propiedades secretas de Streamlit.")
                    st.stop()
                
                api_key = st.secrets["GEMINI_API_KEY"]

                # EXTRAER TEXTO DE LOS APUNTES
                reader_apuntes = pypdf.PdfReader(uploaded_apuntes)
                texto_apuntes = ""
                for page in reader_apuntes.pages:
                    texto_apuntes += page.extract_text() or ""

                # CONFIGURAR PROMPTS ESPECÍFICOS SEGÚN LA ELECCIÓN
                if "Libro" in tipo_recurso:
                    prompt_especifico = """
                    Formato de salida requerido: Un único archivo HTML estructurado y limpio.
                    - Usa obligatoriamente la etiqueta <h1> para los títulos de los Capítulos principales.
                    - Usa la etiqueta <h2> para los Subcapítulos.
                    - Al final de cada sección, añade 3 preguntas de autoevaluación utilizando la etiqueta HTML <details> para ocultar las respuestas y el feedback (retroalimentación).
                    Devuelve EXCLUSIVAMENTE el código HTML. No incluyas marcas de markdown como ```html ni texto explicativo antes o después.
                    """
                    extension = "html"
                    mimetype = "text/html"

                elif "XML" in tipo_recurso:
                    prompt_especifico = """
                    Formato de salida requerido: Un archivo en formato Moodle XML estricto y válido para importar preguntas y contenidos en una Lección de Moodle.
                    - Crea las páginas de contenido con la teoría.
                    - Genera preguntas de opción múltiple (multichoice) bajo el estándar XML de Moodle, incluyendo retroalimentaciones (feedback) específicas para respuestas correctas e incorrectas.
                    Devuelve EXCLUSIVAMENTE el código XML de Moodle estructurado. No agregues texto de saludo o explicaciones fuera del bloque de código XML ni marcas ```xml.
                    """
                    extension = "xml"
                    mimetype = "text/xml"

                else:
                    prompt_especifico = """
                    Formato de salida requerido: Un archivo en formato GIFT (General Import Format Technology) válido para importar preguntas en el Banco de Preguntas de Moodle.
                    Reglas estrictas del formato GIFT:
                    - Cada pregunta empieza con una línea de título entre dobles dos puntos: ::Título de la pregunta::
                    - A continuación va el enunciado de la pregunta.
                    - Las respuestas van entre llaves { }.
                    - La respuesta correcta lleva el signo = delante.
                    - Las respuestas incorrectas llevan el signo ~ delante.
                    - Opcionalmente, añade feedback con #Texto del feedback tras cada opción.
                    - Separa cada pregunta con una línea en blanco.
                    Ejemplo de pregunta correcta:
                    ::Pregunta 1::¿Cuál es la capital de España?{
                    =Madrid #Correcto, Madrid es la capital.
                    ~Barcelona #Incorrecto.
                    ~Sevilla #Incorrecto.
                    ~Valencia #Incorrecto.
                    }
                    Genera al menos 15 preguntas variadas cubriendo todos los temas del documento.
                    Devuelve EXCLUSIVAMENTE el bloque GIFT. Sin marcas ```gift ni texto explicativo o adicional fuera del formato.
                    """
                    extension = "gift.txt"
                    mimetype = "text/plain"

                # EXTRAER TEXTO DE LA SA SI EXISTE
                texto_sa_instruccion = ""
                if uploaded_sa:
                    reader_sa = pypdf.PdfReader(uploaded_sa)
                    texto_sa = ""
                    for page in reader_sa.pages:
                        texto_sa += page.extract_text() or ""
                    
                    texto_sa_instruccion = f"Es OBLIGATORIO que alinees y vincules los contenidos teóricos, el enfoque y el vocabulario con los criterios de evaluación y competencias descritos en este texto de la Situación de Aprendizaje:\n{texto_sa}"
                else:
                    texto_sa_instruccion = "Desarrolla los contenidos con un enfoque competencial e integrado acorde al currículo de Canarias."

                # PROMPT FINAL UNIFICADO
                prompt_base = f"""
                Actúas como un diseñador instruccional de e-learning y asesor pedagógico experto en el currículo de la Consejería de Educación de Canarias.
                
                Debes transformar el siguiente texto de apuntes en bruto en un recurso educativo para la materia de {materia} de {nivel}.
                
                TEXTO DE APUNTES:
                ---
                {texto_apuntes}
                ---

                {texto_sa_instruccion}

                IDIOMA DE SALIDA OBLIGATORIO: Redacta TODO el contenido del recurso (títulos, explicaciones, preguntas, respuestas y feedback) EXCLUSIVAMENTE en {idioma}. No uses ningún otro idioma en ninguna parte del recurso generado.

                {prompt_especifico}
                """

                # --- CONEXIÓN DIRECTA POR HTTP PASANDO DE LIBRERÍAS DE GOOGLE ---
                # Forzamos la URL oficial v1 estable directamente al modelo flash
                # --- CONEXIÓN DIRECTA POR HTTP LIMPIA ---
                # Aplicamos .strip() para eliminar cualquier espacio invisible que rompa la conexión
                api_key_limpia = str(api_key).strip()
                modelo_limpio = str(MODELO).strip()
                
                url = f"https://generativelanguage.googleapis.com/v1/models/{modelo_limpio}:generateContent?key={api_key_limpia}"
                
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt_base}]
                    }]
                }

                # Hacemos la petición web real
                response = requests.post(url, json=payload, headers=headers)
                response_json = response.json()

                # Comprobamos si Google se queja
                if response.status_code != 200:
                    st.error(f"⚠️ Error directo del servidor de Google (Código {response.status_code}):")
                    st.json(response_json)
                    st.stop()

                # Extraemos la respuesta del texto de la estructura JSON de Google
                try:
                    texto_generado = response_json['candidates'][0]['content']['parts'][0]['text']
                except KeyError:
                    st.error("Google respondió, pero la estructura del resultado no fue la esperada:")
                    st.json(response_json)
                    st.stop()

                resultado_limpio = (
                    texto_generado.replace("```html", "")
                    .replace("```xml", "")
                    .replace("```gift", "")
                    .replace("```", "")
                    .strip()
                )

                st.success("¡Recurso generado con éxito!")

                # --- BOTÓN DE DESCARGA ---
                nombre_archivo = f"recurso_{materia.lower().replace(' ', '_')}_{nivel.lower().replace(' ', '_')}.{extension}"
                st.download_button(
                    label=f"📥 Descargar archivo .{extension} para EVAGD",
                    data=resultado_limpio,
                    file_name=nombre_archivo,
                    mime=mimetype,
                    use_container_width=True,
                )

                # --- VISTA PREVIA ---
                if "Libro" in tipo_recurso:
                    st.divider()
                    with st.expander("👁️ Vista previa del HTML generado", expanded=True):
                        components.html(resultado_limpio, height=600, scrolling=True)

                # --- INSTRUCCIONES ---
                st.divider()
                st.info("💡 **¿Cómo subirlo a EVAGD?**")
                if "Libro" in tipo_recurso:
                    st.markdown("""
                    1. Entra a tu aula virtual en **EVAGD** y activa la edición.
                    2. Añade la actividad/recurso **'Libro'**.
                    3. Una vez creado, ve al bloque de *Administración del libro* en el menú lateral y pulsa **'Importar capítulos'**.
                    4. Sube este archivo `.html` y Moodle creará el índice de forma automática.
                    """)
                elif "XML" in tipo_recurso:
                    st.markdown("""
                    1. Entra a tu aula virtual en **EVAGD** y activa la edición.
                    2. Añade la actividad/recurso **'Lección'**.
                    3. Abre la lección recién creada y pulsa en la pestaña **'Importar preguntas'**.
                    4. Selecciona el formato **'Moodle XML'**, arrastra este archivo `.xml` y pulsa importar.
                    """)
                else:
                    st.markdown("""
                    1. Entra a tu aula virtual en **EVAGD** y ve a **Banco de Preguntas** (en el menú de la asignatura).
                    2. Pulsa **'Importar'** y selecciona el formato **'Formato GIFT'**.
                    3. Sube este archivo `.txt` y Moodle importará todas las preguntas automáticamente.
                    4. Luego puedes crear un **Cuestionario** y añadir las preguntas desde el banco.
                    """)

            except Exception as e:
                st.error(f"⚠️ **Error inesperado en la aplicación:** {e}")
