import base64
import io
import json
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


APP_TITLE = "Ficha Cadastral de Membros"
DEFAULT_JSON_FILE = Path(__file__).with_name("exemplo_ficha_membros.json")

IDENTIFICACAO_FIELDS = [
    ("matricula", "Matricula No"),
    ("nome", "Nome *"),
    ("conhecido_como", "Conhecido Como"),
    ("cpf", "CPF *"),
    ("identidade", "Identidade"),
    ("orgao_expedicao", "Orgao Expedicao"),
    ("data_expedicao", "Data Expedicao"),
    ("data_nascimento", "Data de Nascimento *"),
    ("naturalidade", "Naturalidade"),
    ("nacionalidade", "Nacionalidade"),
    ("estado_civil", "Estado Civil"),
    ("grau_instrucao", "Grau de Instrucao"),
    ("origem_religiosa", "Origem Religiosa"),
    ("igreja", "Igreja"),
]

CONTATO_FIELDS = [
    ("telefone_principal", "Telefone Principal"),
    ("telefone_secundario", "Telefone Secundario"),
    ("telefone_recado", "Telefone de Recado"),
    ("email", "E-mail"),
    ("logradouro", "Logradouro"),
    ("numero", "Numero"),
    ("complemento", "Complemento"),
    ("bairro", "Bairro"),
    ("cidade", "Cidade"),
    ("estado", "Estado"),
    ("cep", "CEP"),
]

DADOS_COMPLEMENTARES_FIELDS = [
    ("titulo_eleitor_numero", "Titulo de Eleitor / No"),
    ("titulo_eleitor_zona", "Titulo de Eleitor / Zona"),
    ("titulo_eleitor_secao", "Titulo de Eleitor / Secao"),
    ("reservista", "Reservista"),
    ("tipo_sanguineo", "Tipo Sanguineo"),
    ("certidao", "Cert. Nasc. / Casam."),
    ("carteira_motorista", "Carteira de Motorista"),
    ("profissao", "Profissao"),
    ("cargo", "Cargo"),
    ("data_casamento", "Data de Casamento"),
]

HISTORICO_EVENTOS = [
    "Conversao",
    "Batismo nas Aguas",
    "Batismo no Espirito Santo",
    "Consagracao a Diacono(isa)",
    "Consagracao a Presbitero",
    "Ordenacao a Evangelista",
    "Ordenacao a Pastor(a)",
]

FAMILIARES = ["Pai", "Mae", "Conjuge"]


def empty_data():
    return {
        "campos": {
            **{key: "" for key, _ in IDENTIFICACAO_FIELDS},
            **{key: "" for key, _ in CONTATO_FIELDS},
            **{key: "" for key, _ in DADOS_COMPLEMENTARES_FIELDS},
            "sexo": "Masculino",
            "dirigente": "",
            "chefe_familiar": "Nao",
            "foto_nome": "",
            "foto_base64": "",
        },
        "historico": {evento: {"data": "", "localidade": ""} for evento in HISTORICO_EVENTOS},
        "familiares": {parentesco: {"nome": "", "nascimento": ""} for parentesco in FAMILIARES},
        "observacoes": "",
    }


def merge_data(source):
    merged = empty_data()
    if not source:
        return merged

    for key, value in source.get("campos", {}).items():
        merged["campos"][key] = value

    for evento, values in source.get("historico", {}).items():
        if evento in merged["historico"]:
            merged["historico"][evento]["data"] = values.get("data", "")
            merged["historico"][evento]["localidade"] = values.get("localidade", "")

    for parentesco, values in source.get("familiares", {}).items():
        if parentesco in merged["familiares"]:
            merged["familiares"][parentesco]["nome"] = values.get("nome", "")
            merged["familiares"][parentesco]["nascimento"] = values.get("nascimento", "")

    merged["observacoes"] = source.get("observacoes", "")
    return merged


def load_example_data():
    if DEFAULT_JSON_FILE.exists():
        return merge_data(json.loads(DEFAULT_JSON_FILE.read_text(encoding="utf-8")))
    return empty_data()


def ensure_state():
    if "form_data" not in st.session_state:
        st.session_state.form_data = load_example_data()
    if "form_initialized" not in st.session_state:
        populate_state(st.session_state.form_data)
        st.session_state.form_initialized = True


def set_form_data(data):
    st.session_state.form_data = merge_data(data)


def image_bytes_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")


def decode_photo(data):
    foto_base64 = data["campos"].get("foto_base64", "")
    if not foto_base64:
        return None
    try:
        return base64.b64decode(foto_base64)
    except Exception:
        return None


def collect_data():
    data = empty_data()
    data["campos"]["sexo"] = st.session_state.get("sexo", "Masculino")
    data["campos"]["dirigente"] = st.session_state.get("dirigente", "")
    data["campos"]["chefe_familiar"] = st.session_state.get("chefe_familiar", "Nao")
    data["campos"]["foto_nome"] = st.session_state.get("foto_nome", "")
    data["campos"]["foto_base64"] = st.session_state.get("foto_base64", "")
    data["observacoes"] = st.session_state.get("observacoes", "")

    for key, _label in IDENTIFICACAO_FIELDS + CONTATO_FIELDS + DADOS_COMPLEMENTARES_FIELDS:
        data["campos"][key] = st.session_state.get(key, "")

    for evento in HISTORICO_EVENTOS:
        data["historico"][evento]["data"] = st.session_state.get(f"hist_data_{evento}", "")
        data["historico"][evento]["localidade"] = st.session_state.get(f"hist_local_{evento}", "")

    for parentesco in FAMILIARES:
        data["familiares"][parentesco]["nome"] = st.session_state.get(f"fam_nome_{parentesco}", "")
        data["familiares"][parentesco]["nascimento"] = st.session_state.get(f"fam_nasc_{parentesco}", "")

    return data


def populate_state(data):
    for key, _label in IDENTIFICACAO_FIELDS + CONTATO_FIELDS + DADOS_COMPLEMENTARES_FIELDS:
        st.session_state[key] = data["campos"].get(key, "")

    st.session_state["sexo"] = data["campos"].get("sexo", "Masculino")
    st.session_state["dirigente"] = data["campos"].get("dirigente", "")
    st.session_state["chefe_familiar"] = data["campos"].get("chefe_familiar", "Nao")
    st.session_state["foto_nome"] = data["campos"].get("foto_nome", "")
    st.session_state["foto_base64"] = data["campos"].get("foto_base64", "")
    st.session_state["observacoes"] = data.get("observacoes", "")

    for evento in HISTORICO_EVENTOS:
        st.session_state[f"hist_data_{evento}"] = data["historico"][evento]["data"]
        st.session_state[f"hist_local_{evento}"] = data["historico"][evento]["localidade"]

    for parentesco in FAMILIARES:
        st.session_state[f"fam_nome_{parentesco}"] = data["familiares"][parentesco]["nome"]
        st.session_state[f"fam_nasc_{parentesco}"] = data["familiares"][parentesco]["nascimento"]


def reset_form():
    fresh = empty_data()
    set_form_data(fresh)
    populate_state(fresh)


def draw_pdf(data):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 12 * mm
    line_gap = 5.3 * mm

    def header():
        pdf.setFont("Helvetica-Bold", 15)
        pdf.drawString(margin, height - 16 * mm, "Ficha Cadastral")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(margin, height - 22 * mm, "Igreja Evangelica Assembleia de Deus")
        pdf.setStrokeColor(colors.black)
        pdf.line(margin, height - 24 * mm, width - margin, height - 24 * mm)

    def section(title, y):
        pdf.setFillColor(colors.HexColor("#EFEFEF"))
        pdf.rect(margin, y - 4 * mm, width - (margin * 2), 7 * mm, fill=1, stroke=0)
        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(margin + 2 * mm, y - 1 * mm, title)
        return y - 8 * mm

    def write_label_value(x, y, label, value, label_width=34 * mm):
        pdf.setFont("Helvetica-Bold", 8.5)
        pdf.drawString(x, y, f"{label}:")
        pdf.setFont("Helvetica", 8.5)
        pdf.drawString(x + label_width, y, value or "-")

    def write_two_col(y, left, right):
        write_label_value(margin, y, left[0], left[1])
        write_label_value(width / 2, y, right[0], right[1])
        return y - line_gap

    def draw_photo_box(photo_bytes):
        box_width = 34 * mm
        box_height = 44 * mm
        x = width - margin - box_width
        y_top = height - 30 * mm
        y = y_top - box_height
        pdf.rect(x, y, box_width, box_height, stroke=1, fill=0)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawCentredString(x + (box_width / 2), y_top + 3 * mm, "Foto")

        if not photo_bytes:
            pdf.setFont("Helvetica", 7.5)
            pdf.drawCentredString(x + (box_width / 2), y + (box_height / 2), "Sem foto")
            return

        image = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
        image = ImageOps.fit(image, (220, 280))
        pdf.drawImage(ImageReader(image), x + 1.5 * mm, y + 1.5 * mm, box_width - 3 * mm, box_height - 3 * mm)

    campos = data["campos"]
    photo_bytes = decode_photo(data)

    y = height - 30 * mm
    header()
    draw_photo_box(photo_bytes)

    y = section("Identificacao", y)
    y = write_two_col(y, ("Matricula", campos.get("matricula", "")), ("Nome", campos.get("nome", "")))
    y = write_two_col(y, ("Conhecido como", campos.get("conhecido_como", "")), ("CPF", campos.get("cpf", "")))
    y = write_two_col(y, ("Identidade", campos.get("identidade", "")), ("Orgao expedicao", campos.get("orgao_expedicao", "")))
    y = write_two_col(y, ("Data expedicao", campos.get("data_expedicao", "")), ("Data nascimento", campos.get("data_nascimento", "")))
    y = write_two_col(y, ("Naturalidade", campos.get("naturalidade", "")), ("Nacionalidade", campos.get("nacionalidade", "")))
    y = write_two_col(y, ("Estado civil", campos.get("estado_civil", "")), ("Sexo", campos.get("sexo", "")))
    y = write_two_col(y, ("Grau instrucao", campos.get("grau_instrucao", "")), ("Origem religiosa", campos.get("origem_religiosa", "")))
    y = write_two_col(y, ("Igreja", campos.get("igreja", "")), ("Dirigente", campos.get("dirigente", "")))

    y = section("Contato e Endereco", y - 2 * mm)
    y = write_two_col(y, ("Telefone principal", campos.get("telefone_principal", "")), ("Telefone secundario", campos.get("telefone_secundario", "")))
    y = write_two_col(y, ("Telefone recado", campos.get("telefone_recado", "")), ("E-mail", campos.get("email", "")))
    y = write_two_col(y, ("Logradouro", campos.get("logradouro", "")), ("Numero", campos.get("numero", "")))
    y = write_two_col(y, ("Complemento", campos.get("complemento", "")), ("Bairro", campos.get("bairro", "")))
    y = write_two_col(y, ("Cidade", campos.get("cidade", "")), ("Estado", campos.get("estado", "")))
    y = write_two_col(y, ("CEP", campos.get("cep", "")), ("Chefe familiar", campos.get("chefe_familiar", "")))

    y = section("Dados Complementares", y - 2 * mm)
    y = write_two_col(y, ("Titulo eleitor no", campos.get("titulo_eleitor_numero", "")), ("Zona", campos.get("titulo_eleitor_zona", "")))
    y = write_two_col(y, ("Secao", campos.get("titulo_eleitor_secao", "")), ("Reservista", campos.get("reservista", "")))
    y = write_two_col(y, ("Tipo sanguineo", campos.get("tipo_sanguineo", "")), ("Certidao", campos.get("certidao", "")))
    y = write_two_col(y, ("CNH", campos.get("carteira_motorista", "")), ("Profissao", campos.get("profissao", "")))
    y = write_two_col(y, ("Cargo", campos.get("cargo", "")), ("Data casamento", campos.get("data_casamento", "")))
    y = write_two_col(y, ("Foto arquivo", campos.get("foto_nome", "")), ("Igreja origem", campos.get("igreja", "")))

    y = section("Historico da Pessoa", y - 2 * mm)
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawString(margin, y, "Ocorrencia")
    pdf.drawString(margin + 75 * mm, y, "Data")
    pdf.drawString(margin + 105 * mm, y, "Localidade")
    y -= line_gap
    pdf.setFont("Helvetica", 8.5)
    for evento in HISTORICO_EVENTOS:
        item = data["historico"][evento]
        pdf.drawString(margin, y, evento)
        pdf.drawString(margin + 75 * mm, y, item.get("data", "") or "-")
        pdf.drawString(margin + 105 * mm, y, item.get("localidade", "") or "-")
        y -= line_gap

    y = section("Familiares", y - 2 * mm)
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawString(margin, y, "Parentesco")
    pdf.drawString(margin + 35 * mm, y, "Nome")
    pdf.drawString(margin + 120 * mm, y, "Nascimento")
    y -= line_gap
    pdf.setFont("Helvetica", 8.5)
    for parentesco in FAMILIARES:
        item = data["familiares"][parentesco]
        pdf.drawString(margin, y, parentesco)
        pdf.drawString(margin + 35 * mm, y, item.get("nome", "") or "-")
        pdf.drawString(margin + 120 * mm, y, item.get("nascimento", "") or "-")
        y -= line_gap

    y = section("Observacoes", y - 2 * mm)
    text_object = pdf.beginText(margin, y)
    text_object.setFont("Helvetica", 8.5)
    for line in (data.get("observacoes", "") or "-").splitlines()[:8]:
        text_object.textLine(line)
    pdf.drawText(text_object)

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def render_text_fields(title, fields):
    st.subheader(title)
    col1, col2 = st.columns(2)
    for index, (key, label) in enumerate(fields):
        target_col = col1 if index % 2 == 0 else col2
        with target_col:
            st.text_input(label, key=key)


def render_history_section():
    st.subheader("Historico da Pessoa")
    for evento in HISTORICO_EVENTOS:
        cols = st.columns([1.2, 1, 1])
        cols[0].markdown(f"**{evento}**")
        cols[1].text_input("Data", key=f"hist_data_{evento}", label_visibility="collapsed", placeholder="Data")
        cols[2].text_input("Localidade", key=f"hist_local_{evento}", label_visibility="collapsed", placeholder="Localidade")


def render_family_section():
    st.subheader("Familiares")
    for parentesco in FAMILIARES:
        cols = st.columns([0.8, 1.5, 1])
        cols[0].markdown(f"**{parentesco}**")
        cols[1].text_input("Nome", key=f"fam_nome_{parentesco}", label_visibility="collapsed", placeholder="Nome")
        cols[2].text_input("Nascimento", key=f"fam_nasc_{parentesco}", label_visibility="collapsed", placeholder="Nascimento")


def render_photo_section():
    st.subheader("Foto")
    upload = st.file_uploader("Envie a foto do membro", type=["png", "jpg", "jpeg", "webp"], key="foto_upload")
    if upload is not None:
        photo_bytes = upload.getvalue()
        st.session_state["foto_base64"] = image_bytes_to_base64(photo_bytes)
        st.session_state["foto_nome"] = upload.name

    photo_bytes = decode_photo({"campos": st.session_state})
    if photo_bytes:
        st.image(photo_bytes, width=180)
        st.caption(st.session_state.get("foto_nome", "foto"))
    else:
        st.info("Nenhuma foto selecionada.")

    if st.button("Remover foto", use_container_width=True):
        st.session_state["foto_base64"] = ""
        st.session_state["foto_nome"] = ""
        st.rerun()


def render_sidebar():
    st.sidebar.header("Acoes")

    if st.sidebar.button("Carregar exemplo", use_container_width=True):
        data = load_example_data()
        set_form_data(data)
        populate_state(data)
        st.rerun()

    if st.sidebar.button("Limpar formulario", use_container_width=True):
        reset_form()
        st.rerun()

    uploaded_json = st.sidebar.file_uploader("Importar JSON", type=["json"])
    if uploaded_json is not None:
        try:
            imported = merge_data(json.load(uploaded_json))
            set_form_data(imported)
            populate_state(imported)
            st.sidebar.success("JSON carregado com sucesso.")
        except Exception:
            st.sidebar.error("Nao foi possivel ler o arquivo JSON.")


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    ensure_state()
    render_sidebar()

    st.title(APP_TITLE)
    st.caption("Versao web compativel com Streamlit Cloud.")

    top_left, top_right = st.columns([2, 1])
    with top_left:
        render_text_fields("Identificacao", IDENTIFICACAO_FIELDS)
        st.radio("Sexo", ["Masculino", "Feminino"], key="sexo", horizontal=True)
    with top_right:
        render_photo_section()

    render_text_fields("Contato e Endereco", CONTATO_FIELDS)
    render_text_fields("Dados Complementares", DADOS_COMPLEMENTARES_FIELDS)

    st.subheader("Informacoes Complementares")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Dirigente", key="dirigente")
    with col2:
        st.radio("Chefe Familiar?", ["Sim", "Nao"], key="chefe_familiar", horizontal=True)

    st.text_area("Observacoes", key="observacoes", height=120)

    render_history_section()
    render_family_section()

    data = collect_data()
    st.session_state.form_data = data
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    pdf_bytes = draw_pdf(data)

    action1, action2 = st.columns(2)
    action1.download_button(
        "Baixar JSON",
        data=json_bytes,
        file_name="ficha_membros_dados.json",
        mime="application/json",
        use_container_width=True,
    )
    action2.download_button(
        "Baixar PDF",
        data=pdf_bytes,
        file_name="ficha_membros_preenchida.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
