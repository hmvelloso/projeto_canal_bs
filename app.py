import pandas as pd
import os
import streamlit as st
import math
import numpy as np

import matplotlib
matplotlib.use("Agg")  # backend headless pro Streamlit Cloud

import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg



def add_image(ax, img_path, xy, zoom=0.08, box_alignment=(0.5, 0.5), xybox=(0, 0), xycoords="data"):
    """Cola uma imagem no ponto xy. xybox desloca em pixels (dx, dy)."""
    if not img_path or not os.path.exists(img_path):
        return

    img = mpimg.imread(img_path)
    imagebox = OffsetImage(img, zoom=zoom)

    ab = AnnotationBbox(
        imagebox,
        xy,
        xybox=xybox,
        xycoords=xycoords,          # <- agora dá pra mudar!
        boxcoords="offset points",
        frameon=False,
        box_alignment=box_alignment,
        clip_on=False
    )
    ax.add_artist(ab)

def get_notas(jogo_filename):
    file_path = 'jogos/' + jogo
    with open(file_path, 'r', encoding='utf-8') as jogo_csv:
        lines = jogo_csv.readlines()
        date = lines[0].split(',')[1]
        competition = lines[1].split(',')[1]
        vs = lines[2].split(',')[1]
        location = lines[3].split(',')[1]

    notas_jogo_df = pd.read_csv(file_path, sep=',', skiprows=5)
    notas_jogo_df['Data'] = date
    notas_jogo_df['Competição'] = competition
    notas_jogo_df['VS'] = vs
    notas_jogo_df['Local'] = location
    notas_jogo_df['Data (Ano)'] = date[:4]

    return notas_jogo_df

def notas_por_pessoa(df, nome, datas):
    return (
        df[df["Nota por"] == nome]
        .set_index("Data")
        .reindex(datas)["Nota"]
        .tolist()
    )
def get_escudos(df_jogador, datas, times_dict):
    escudos = []
    for data_jogo in datas:
        time = df_jogador[df_jogador['Data'] == data_jogo]['VS'].to_list()[0]
        escudos.append(times_dict[time])

    return escudos

def get_competicao(sigla, competicao_df):
    return competicao_df[competicao_df['Sigla'] == sigla]['Competição'].values[0]

def split_list(list_to_split, n_elements):
    final_list = []
    section_list = []
    for element in list_to_split:
        section_list.append(element)
        if len(section_list) == n_elements:
            final_list.append(section_list)
            section_list = []
    if len(section_list) > 0:
        final_list.append(section_list)

    return final_list

def list_jogos(jogos_df, competicoes_df):
    jogos_list = []
    for data_jogo in jogos_df.Data.unique():
        jogo_atual_df = jogos_df[jogos_df['Data'] == data_jogo]
        notas_por = jogo_atual_df['Nota por'].str.cat(sep=' e ')
        time_vs = jogo_atual_df.VS.to_list()[0]
        competicao = get_competicao(jogo_atual_df.Competição.to_list()[0], competicoes_df)
        ano = jogo_atual_df.Data.to_list()[0][:4]
        # print(jogo_atual_df.Local.to_list()[0])
        if jogo_atual_df.Local.to_list()[0] == 'F':
            jogo = time_vs + ' x Flamengo'
        else:
            jogo = 'Flamengo x ' + time_vs

        jogos_list.append(jogo + ' - ' + competicao + ' ' + ano + ' (' + notas_por + ')')
    return jogos_list

def custom_round(x, prec=1, base=.5):
  return round(base * round(float(x)/base),prec)

def select_quiz(selected_quiz):
    st.session_state['quiz_selecionado'] = selected_quiz
    if selected_quiz == 0:
        reset_quiz_questions()
        reset_quiz_notas()

def submit_quiz_notas():
    st.session_state['show_resultados'] = True

def reset_quiz_notas():
    st.session_state['show_resultados'] = False


def finalize_quiz(answer_index):
    check_answer(answer_index)
    reset_answered()
    st.session_state['all_answered'] = True

def check_answer(answer_index):
    correct_answer = st.session_state['questions'][st.session_state['question_index']]['correct_idx']
    if correct_answer == answer_index:
        st.session_state['questions'][st.session_state['question_index']]['selected_correct'] = 1

def reset_quiz_questions():
    st.session_state['question_index'] = 0
    st.session_state['all_answered'] = False
    for actual_question in st.session_state['questions']:
        actual_question['selected_correct'] = 0

def next_question(answer_index):
    check_answer(answer_index)
    reset_answered()
    st.session_state['question_radio'] = None
    if st.session_state['question_index'] < 9:
        st.session_state['question_index'] += 1
        st.session_state.pop('question_radio', None)
    else:
        st.session_state['question_index'] = 9

def previous_question():
    if st.session_state['question_index'] > 0:
        st.session_state['question_index'] -= 1
    else:
        st.session_state['question_index'] = 0

def reset_answered():
    st.session_state['answered'] = False

def set_as_answered():
    st.session_state['answered'] = True

competicoes_df = pd.read_csv(r'metadados/competições.csv', sep=',')
jogadores_df = pd.read_csv(r'metadados/jogadores.csv', sep=',')

competicao_dict = {}
for competicao in competicoes_df.itertuples():
    competicao_dict[competicao[1]] = {'name': competicao[2], 'logo':competicao[3]}

times_dict = {}
flag = True
with open('metadados/times.csv', 'r', encoding='utf-8') as f:
    for time in f:
        if flag:
            flag = False
        else:
            dados = time.strip().split(',')
            times_dict[dados[0]] = dados[1]


jogos_df = pd.DataFrame()
for jogo in sorted(os.listdir('jogos'))[1:]:
    jogos_df = pd.concat([jogos_df, get_notas(jogo)], ignore_index=True)

st.dataframe(jogos_df)

valores_default = {
    'filter_ano': sorted(jogos_df['Data (Ano)'].unique()),
    'filter_competicoes': competicoes_df['Competição'].to_list(),
    'filter_simoes': True,
    'filter_b10': True
}

perguntas_quiz = [
    {
        'question': 'Qual foi o melhor jogador da Libertadores 2025?',
        'choices': ['Opção 1', 'Opção 2', 'Opção 3', 'Opção 4'],
        'correct_idx': 0,
        'selected_correct': 0,
        'comment': ''
    },
    {
        'question': 'Qual foi o melhor jogador do BR 2025?',
        'choices': ['Opção 1', 'Opção 2', 'Opção 3', 'Opção 4'],
        'correct_idx': 1,
        'selected_correct': 0,
        'comment': ''
    },
    {
        'question': 'Qual jogador já teve a maior distância entre sua maior e menor nota em um ano?',
        'choices': ['Opção 1', 'Opção 2', 'Opção 3', 'Opção 4'],
        'correct_idx': 2,
        'selected_correct': 0,
        'comment': ''
    },
    {
        'question': 'Qual o jogo de melhor média do time em 2025?',
        'choices': ['Opção 1', 'Opção 2', 'Opção 3', 'Opção 4'],
        'correct_idx': 3,
        'selected_correct': 0,
        'comment': ''
    },
    {
        'question': 'Qual jogador levou mais o prêmio nem Noé em 2024?',
        'choices': ['Opção 1', 'Opção 2', 'Opção 3', 'Opção 4'],
        'correct_idx': 0,
        'selected_correct': 0,
        'comment': ''
    },
    {
        'question': 'Qual o jogador mais regular em 2025?',
        'choices': ['Opção 1', 'Opção 2', 'Opção 3', 'Opção 4'],
        'correct_idx': 1,
        'selected_correct': 0,
        'comment': ''
    },
    {
        'question': 'Qual jogador mais irritou o Simões em 2025?',
        'choices': ['Opção 1', 'Opção 2', 'Opção 3', 'Opção 4'],
        'correct_idx': 2,
        'selected_correct': 0,
        'comment': ''
    },
    {
        'question': 'Qual jogador teve mais vezes a maior nota da partida em 2025?',
        'choices': ['Opção 1', 'Opção 2', 'Opção 3', 'Opção 4'],
        'correct_idx': 3,
        'selected_correct': 0,
        'comment': ''
    },
    {
        'question': 'Qual jogador teve mais vezes a menor nota da partida em 2025?',
        'choices': ['Opção 1', 'Opção 2', 'Opção 3', 'Opção 4'],
        'correct_idx': 0,
        'selected_correct': 0,
        'comment': ''
    },
    {
        'question': 'Pergunta 10',
        'choices': ['Opção 1', 'Opção 2', 'Opção 3', 'Opção 4'],
        'correct_idx': 0,
        'selected_correct': 0,
        'comment': ''
    }
]


for filter_key in valores_default.keys():
    if filter_key not in st.session_state:
        st.session_state[filter_key] = valores_default[filter_key]

if 'quiz_selecionado' not in st.session_state:
    st.session_state['quiz_selecionado'] = 0
    # 0 é nenhum quiz
    # 1 é quiz de notas
    # 2 é quiz de perguntas

if 'question_index' not in st.session_state:
    st.session_state['question_index'] = 0

if 'questions' not in st.session_state:
    st.session_state['questions'] = perguntas_quiz

if 'all_answered' not in st.session_state:
    st.session_state['all_answered'] = False

if 'answered' not in st.session_state:
    st.session_state['answered'] = False

if 'question_radio' not in st.session_state:
    st.session_state['question_radio'] = None


bg_img_css = """
.stApp {
    background: 
           linear-gradient(
               rgba(0, 0, 0, 0.75),
               rgba(0, 0, 0, 0.75)
           ),
           url("https://admin.cnnbrasil.com.br/wp-content/uploads/sites/12/2025/11/flamengo-campeao-libertadores.jpg?w=1200&h=675&crop=1");
    background-size: cover;
    background-attachment: fixed; /* Keeps the background fixed during scrolling */
}

/* Add an opaque overlay color to "dim" the background image */
.stApp::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7); /* Black overlay with 50% opacity */
    z-index: -1; /* Place the overlay behind the content */
}}
"""

st.markdown('<style>' + bg_img_css + '</style>', unsafe_allow_html=True)

st.image('media/canal/logo_canal.jpg', width=100)

st.title("Notas do Canal Bruninho e Simões")
st.write("Aqui estão listadas todas as notas dadas nas lives pós-jogos do Flamengo")

####### START FILTER SECTION

with st.expander("Filtros"):
    spacer_col, filter_reset_col = st.columns([0.8, 0.2])
    if filter_reset_col.button('Limpar filtros'):
        for filter_key in valores_default.keys():
            st.session_state[filter_key] = valores_default[filter_key]

    filter_cl1, filter_cl2 = st.columns(2)
    # FILTER COLUMN 1
    selected_ano = filter_cl1.multiselect(
        'Selecione um ano',
        sorted(jogos_df['Data (Ano)'].unique()),
        default=sorted(jogos_df['Data (Ano)'].unique()),
        key='filter_ano'
    )

    # FILTER COLUMN 2
    filter_container = filter_cl2.container()
    filter_container.write('Notas por')
    show_notas_simoes = filter_container.checkbox('Simões', value=valores_default['filter_simoes'], key='filter_simoes')
    show_notas_b10 = filter_container.checkbox('B10', value=valores_default['filter_b10'], key='filter_b10')

    cols = st.columns(len(competicao_dict))

    st.write('Escolha as competições')
    compet_col1, compet_col2 = st.columns(2)
    compet_selected = compet_col1.multiselect(
        "competition_multiselect",
        sorted(competicoes_df['Competição'].to_list()),
        default=competicoes_df['Competição'].to_list(),
        label_visibility='collapsed',
        key='filter_competicoes'
    )
    siglas = competicoes_df[competicoes_df['Competição'].isin(compet_selected)]['Sigla'].to_list()


    logos = competicoes_df[competicoes_df['Competição'].isin(compet_selected)]['Logo'].to_list()
    n_columns_logos = 4
    for row in split_list(logos, n_columns_logos):
        selected_logos_cols = compet_col2.columns(n_columns_logos)
        for idx, logo in enumerate(row):
            selected_logos_cols[idx].image(logo)

####### END FILTER SECTION

# PAGE BODY
tab_quiz, tab_time, tab_jogador = st.tabs(["Quiz", "Time", "Jogador"])

with tab_quiz:
    match st.session_state['quiz_selecionado']:
        case 0: # Menu de seleção do quiz
            st.markdown("<br><br>", unsafe_allow_html=True)
            col_left, col_center1, col_center2, col_right = st.columns([1, 2, 2, 1])
            col_center1.button(
                'Notas por jogador',
                on_click=select_quiz,
                args=[1]
            )
            col_center2.button(
                'Quiz de 10 perguntas',
                on_click=select_quiz,
                args=[2]
            )
        case 1: # Quiz de notas
            st.button(
                ' < Voltar',
                on_click=select_quiz,
                args=[0]
            )

            st.markdown(
                'Estão sendo considerados jogadores que jogaram:<br>'
                '\tEm: ' + ', '.join(sorted(selected_ano)) + '<br>'
                '\tNas competições: ' + ', '.join(sorted(compet_selected)) + '<br>',
                unsafe_allow_html=True,
            )

            with st.expander('Configurações do quiz'):
                col1, col2 = st.columns(2)

                col1.write('Quer tentar com quantos jogadores? (deixe 0 para todos)')
                col2.write('Jogadores que mais jogaram ou ordem aleatória?')

                col1, col2 = st.columns(2)
                qtd_jogadores = col1.number_input(
                    'qtd_jogadores',
                    min_value=0,
                    max_value=len(jogadores_df),
                    value=10,
                    step=1,
                    label_visibility = 'collapsed'
                )

                toggle_col, label_col = col2.columns([0.1,0.9])
                ordem_jogadores = toggle_col.toggle(
                    'ordem_jogadores',
                    key='toggle_jogadores',
                    label_visibility = 'collapsed',
                    value=True
                )

                if ordem_jogadores:
                    label_col.markdown("Jogadores que mais jogaram")
                else:
                    label_col.markdown("Ordem aleatória")

            jogadores_por_num_jogo = pd.pivot_table(jogos_df,
                                                    values='Nota',
                                                    index='Jogador',
                                                    columns='Nota por',
                                                    aggfunc='count'
                                                    )
            jogadores_por_num_jogo['Max participação'] = jogadores_por_num_jogo[['Simões','B10']].max(axis=1)

            if qtd_jogadores == 0:
                sample_size = len(jogadores_por_num_jogo)
            else:
                sample_size = qtd_jogadores

            if ordem_jogadores:
                ordered_df = jogadores_por_num_jogo.sort_values(by='Max participação', ascending=False)
            else:
                ordered_df = jogadores_por_num_jogo.sample(frac=1)

            top_jogadores = []
            for jogador in ordered_df.head(sample_size).index.tolist():
                top_jogadores.append(
                    {
                        'nome': jogador,
                        'nota_guessed': 0,
                        'nota_real': custom_round(jogos_df[jogos_df['Jogador'] == jogador]['Nota'].mean())
                    }
                )

            if 'show_resultados' not in st.session_state:
                st.session_state['show_resultados'] = False

            # st.write(top_jogadores)
            for jogador in top_jogadores:
                foto_jogador_col, slider_col, resultado_col = st.columns([0.3, 0.4, 0.3])
                col_left, col_center, col_right = foto_jogador_col.columns([1, 3, 1])
                col_center.image(jogadores_df[jogadores_df['Jogador'] == jogador['nome']]['Image Link'].to_list()[0],
                                       width=125)
                foto_jogador_col.markdown(
                    "<span style='text-align: center;'>" + jogador['nome'] + "</span>",
                    unsafe_allow_html=True,
                    text_alignment='center'
                )
                jogador['nota_guessed'] = slider_col.slider('Nota',
                                                            min_value=0.0,
                                                            max_value=10.0,
                                                            step=0.5,
                                                            key=jogador['nome'].replace(' ', '_') + '_slider',
                                                            disabled=st.session_state['show_resultados'],
                                                            )
                if st.session_state['show_resultados']:
                    resultado_nota_col, resultado_diff_col = resultado_col.columns(2)
                    resultado_nota_col.markdown(
                        "<span style='font-size: 3rem'>" + str(jogador['nota_real']) + "</span>",
                        unsafe_allow_html=True
                    )
                    diff_nota = jogador['nota_guessed'] - jogador['nota_real']
                    if diff_nota == 0:
                        nota_icon = ':trophy:'
                    else:
                        nota_icon = ':x:'

                    resultado_diff_col.markdown(
                        "<span style='font-size: 3rem'>" + nota_icon + "</span>",
                        unsafe_allow_html=True
                    )

            soma_guessed = sum(jogador['nota_guessed'] for jogador in top_jogadores)
            soma_real = sum(jogador['nota_real'] for jogador in top_jogadores)

            resultado_final = (soma_guessed - soma_real)/len(top_jogadores)

            if st.session_state['show_resultados']:
                st.markdown(
                    "<span style='font-size: 2rem;text-align: center;'> **Diferença média das notas: " + str(round(resultado_final, 2)) + "**</span>",
                    unsafe_allow_html=True,
                    width='stretch',
                    text_alignment='center'
                )

            col_left, col_center1, col_center2, col_right = st.columns([2, 1, 1, 2])

            col_center1.button(
                'Submeter respostas',
                on_click=submit_quiz_notas,
                disabled= st.session_state['show_resultados'],
            )

            col_center2.button(
                'Limpar notas',
                on_click=reset_quiz_notas,
                icon='🔄',
                disabled= not st.session_state['show_resultados']
            )
        case 2: # Quiz de perguntas
            st.button(
                ' < Voltar',
                on_click=select_quiz,
                args=[0]
            )
            # st.markdown(
            #     "<span style='font-size: 1.2rem'>**Deseja considerar só a teporada 25 ou todas as notas?**</span>",
            #     unsafe_allow_html=True
            # )
            # toggle_col, label_col = st.columns([0.05, 0.95])
            # temporada_perguntas = toggle_col.toggle(
            #     '',
            #     key='toggle_temporada',
            #     label_visibility='collapsed',
            #     value=True
            # )
            #
            # if temporada_perguntas:
            #     label_str = 'Temporada 2025'
            # else:
            #     label_str = 'Todas as temporadas'
            # label_col.markdown(label_str)

            if not st.session_state['all_answered']:
                col_left, col_center, col_right = st.columns([1, 4, 1])
                col_center.markdown(
                    "<span style='font-size: 1.5rem'>" +
                    st.session_state['questions'][st.session_state['question_index']]['question'] +
                    "</span>",
                    unsafe_allow_html=True
                )
                selected_option = col_center.radio(
                    'selected_option',
                    st.session_state['questions'][st.session_state['question_index']]['choices'],
                    index=None,
                    key='question_radio',
                    on_change=set_as_answered,
                    label_visibility="collapsed"
                )

                if selected_option:
                    selected_option_idx = st.session_state['questions'][st.session_state['question_index']]['choices'].index(selected_option)
                else:
                    selected_option_idx = -1

                col_left, col_center, col_right = st.columns([3, 1, 3])
                # col_center1.button(
                #     'Anterior',
                #     on_click=previous_question,
                #     disabled=st.session_state['question_index'] <= 0,
                # )

                button_str ='Próxima' if st.session_state['question_index'] < 9 else 'Finalizar'

                col_center.button(
                    button_str,
                    on_click=next_question if st.session_state['question_index'] < 9 else finalize_quiz,
                    disabled= not st.session_state['answered'],
                    args=[selected_option_idx]
                )

            else:
                nota_final = sum(actual_question['selected_correct'] for actual_question in st.session_state['questions'])
                st.markdown(
                    "<span style='font-size: 4rem;text-align: center;'>**Sua nota é**</span>",
                    unsafe_allow_html=True,
                    text_alignment='center'
                )
                st.markdown(
                    "<span style='font-size: 9rem;text-align: center;'>" + str(nota_final) + "/10</span>",
                    unsafe_allow_html=True,
                    text_alignment='center'
                )
                msg_final = ''
                match nota_final:
                    case 0:
                        msg_final = 'Pow, é sério que você piticou assim? :disappointed:'
                    case 1, 2, 3:
                        msg_final = 'É volante Allan.... Tá complicado.... :unamused:'
                    case 4, 5:
                        msg_final = 'Hoje foi dia de Sampaoli 2023 🥊'
                    case 7, 8:
                        msg_final = 'Flamengo x Santos 25. O resultado tá ótimo, mas passou uns sustos :sweat_smile:'
                    case 9:
                        msg_final = 'Flamengo x PSG. Foi no detalhe :2nd_place_medal:'
                    case 10:
                        msg_final = 'Mais um golaço do Danilo de cabeça! :trophy:'

                st.markdown(
                    "<span style='font-size: 3rem;text-align: center;'>" + msg_final + "</span>",
                    unsafe_allow_html=True,
                    text_alignment='center'
                )
                col_left, col_center, col_right = st.columns([1, 4, 1])
                if nota_final == 10:
                    col_center.image('https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExcmQwdXNtOGFqNTl2cHJxM3ppbHFnazRram11c2JuaHd1eGp4NWNjdyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/EQSjwNQayEjLCPgGWz/giphy.gif')

with tab_time:
    st.markdown('#### Como você prefere ver os dados?', unsafe_allow_html=True)
    tipo_visualizacao = st.radio(
        "radio_visualization_selection",
        ['Por mês', 'Por jogo'],
        label_visibility='collapsed',
        horizontal=True,
        index=0,
        # on_change=st.rerun()
    )

    jogos_time_df = jogos_df

    if selected_ano:
        jogos_time_df = jogos_time_df[jogos_time_df['Data (Ano)'].isin(selected_ano)]

    if siglas:
        jogos_time_df = jogos_time_df[jogos_time_df['Competição'].isin(siglas)]

    show_charts = True
    if not selected_ano or not siglas:
        jogos_time_df = pd.DataFrame()
        show_charts = False

    if show_charts:
        if tipo_visualizacao == 'Por mês':
            ordem_colunas_mes = [
                'Mês/Ano',
                'Média',
                'Maior nota',
                'Jogador (max)',
                'Menor nota',
                'Jogador (min)'
            ]

            jogos_time_df["Data"] = pd.to_datetime(jogos_time_df["Data"])
            jogos_time_df["Mês/Ano"] = jogos_time_df["Data"].dt.to_period("M").dt.strftime("%m/%y")

            st.dataframe(jogos_time_df)

            idx_max = jogos_time_df.groupby("Mês/Ano")["Nota"].idxmax()
            idx_min = jogos_time_df.groupby("Mês/Ano")["Nota"].idxmin()

            max_players = jogos_time_df.loc[idx_max, ["Mês/Ano"] + ["Jogador"]].rename(
                columns={"Jogador": "Jogador (max)"})
            min_players = jogos_time_df.loc[idx_min, ["Mês/Ano"] + ["Jogador"]].rename(
                columns={"Jogador": "Jogador (min)"})

            df_mes = (
                jogos_time_df.groupby("Mês/Ano", as_index=False)
                .agg(
                    media_nota=("Nota", "mean"),
                    nota_min=("Nota", "min"),
                    nota_max=("Nota", "max"),
                ).rename(
                    columns={
                        'media_nota': 'Média',
                        'nota_min': 'Menor nota',
                        'nota_max': 'Maior nota'
                    }
                ).merge(
                    max_players, on="Mês/Ano", how="left"
                ).merge(
                    min_players, on="Mês/Ano", how="left"
                ).round(1)[ordem_colunas_mes]
            )
            with st.expander('Tabela de notas'):
                st.dataframe(df_mes)

            meses = jogos_time_df['Mês/Ano'].unique()

            dados = [
                jogos_time_df.loc[jogos_time_df["Mês/Ano"] == m, "Nota"].dropna()
                for m in meses
            ]

            fig, ax = plt.subplots(figsize=(7, 4), dpi=200)

            ax.boxplot(
                dados,
                tick_labels=[str(m) for m in meses],  # "2024-03", "2024-04", ...
                patch_artist=True
            )

            ax.set_ylim(0, 10)
            ax.set_yticks(range(0, 11, 1))
            ax.set_ylabel("Nota")
            ax.set_title("Distribuição das notas por mês")

            ax.yaxis.grid(True, linestyle="--", alpha=0.25)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            idx_mes_max = df_mes["Média"].idxmax()
            idx_mes_min = df_mes["Média"].idxmin()

            maior_nota_mes = df_mes["Média"].max()
            menor_nota_mes = df_mes["Média"].min()

            mes_maior_nota = df_mes.iloc[idx_mes_max]['Mês/Ano']
            mes_menor_nota = df_mes.iloc[idx_mes_min]['Mês/Ano']

            competicoes_mes_maior_nota = jogos_time_df[jogos_time_df['Mês/Ano'] == mes_maior_nota]['Competição'].unique()
            competicoes_mes_menor_nota = jogos_time_df[jogos_time_df['Mês/Ano'] == mes_menor_nota]['Competição'].unique()

            best_month_col, worst_month_col = st.columns(2)
            best_month_col.markdown(
                "<span style='font-size: 2.5rem;text-align: center;'><b>Melhor mês</b></span>",
                unsafe_allow_html=True,
                text_alignment='center'
            )
            best_month_col.markdown(
                "<span style='font-size: 2rem;text-align: center;'>" + mes_maior_nota + "</span><br>"
                "<span style='font-size: 1.75rem;text-align: center;'>" + ', '.join(competicoes_mes_maior_nota) + "</span>",
                unsafe_allow_html=True,
                text_alignment='center'
            )
            best_month_col.markdown(
                "Nota média<br><span style='font-size: 4rem;text-align: center;'>" + str(maior_nota_mes) + "</span>",
                unsafe_allow_html=True,
                text_alignment='center'
            )

            worst_month_col.markdown(
                "<span style='font-size: 2.5rem;text-align: center;'><b>Pior mês</b></span>",
                unsafe_allow_html=True,
                text_alignment='center'
            )
            worst_month_col.markdown(
                "<span style='font-size: 2rem;text-align: center;'>" + mes_menor_nota + "</span><br>"
                "<span style='font-size: 1.75rem;text-align: center;'>" + ', '.join(competicoes_mes_menor_nota) + "</span>",
                unsafe_allow_html=True,
                text_alignment='center'
            )
            worst_month_col.markdown(
                "Nota média<br><span style='font-size: 4rem;text-align: center; margin:0'>" + str(menor_nota_mes) + "</span>",
                unsafe_allow_html=True,
                text_alignment='center'
            )

        if tipo_visualizacao == 'Por jogo':
            group_by_columns = ["Data", 'VS', 'Competição', 'Local']

            jogos_time_df['Competição'] = jogos_time_df['Competição'].map(competicoes_df.set_index('Sigla')['Competição'])

            idx_max = jogos_time_df.groupby(group_by_columns)["Nota"].idxmax()
            idx_min = jogos_time_df.groupby(group_by_columns)["Nota"].idxmin()

            max_players = jogos_time_df.loc[idx_max, group_by_columns + ["Jogador"]].rename(columns={"Jogador": "Jogador (max)"})
            min_players = jogos_time_df.loc[idx_min, group_by_columns + ["Jogador"]].rename(columns={"Jogador": "Jogador (min)"})

            ordem_colunas_jogos = [
                'Data',
                'VS',
                'Competição',
                'Local',
                'Média',
                'Maior nota',
                'Jogador (max)',
                'Menor nota',
                'Jogador (min)'
            ]

            with st.expander('Tabela de notas'):
                notas_por_jogo = jogos_time_df.groupby(
                        group_by_columns,
                        as_index=False
                    ).agg(
                        media_nota=("Nota", "mean"),
                        nota_min=("Nota", "min"),
                        nota_max=("Nota", "max")
                    ).rename(
                        columns={
                            'media_nota': 'Média',
                            'nota_min': 'Menor nota',
                            'nota_max': 'Maior nota'
                        }
                    ).merge(
                        max_players, on=group_by_columns, how="left"
                    ).merge(
                        min_players, on=group_by_columns, how="left"
                    ).round(1)[ordem_colunas_jogos]

                st.dataframe(
                    notas_por_jogo
                )

            jogos_time_df["Data"] = pd.to_datetime(jogos_time_df["Data"])
            datas = sorted(jogos_time_df["Data"].unique())

            # agrupar notas por data
            dados = [
                jogos_time_df.loc[jogos_time_df["Data"] == d, "Nota"].dropna()
                for d in datas
            ]

            fig, ax = plt.subplots(figsize=(7, 4), dpi=200)

            ax.boxplot(
                dados,
                tick_labels=[d.strftime("%d/%m") for d in datas],
                patch_artist=True,
                boxprops=dict(facecolor="#e6e6e6", edgecolor="#555"),
                medianprops=dict(color="black", linewidth=2),
                whiskerprops=dict(color="#555"),
                capprops=dict(color="#555")
            )

            escudos = get_escudos(jogos_time_df, datas, times_dict)
            positions = np.arange(1, len(datas) + 1)

            # eixo Y
            ax.set_ylim(0, 10)
            ax.set_yticks(range(0, 11))
            ax.set_ylabel("Nota")

            # eixo X: remove texto
            ax.set_xticks(positions)
            ax.set_xticklabels([""] * len(datas))

            # --- escudos no eixo X ---
            y_axes = -0.03  # posição abaixo do eixo (em fração do eixo)

            for pos, escudo_path in zip(positions, escudos):
                add_image(
                    ax,
                    escudo_path,
                    (pos, y_axes),
                    zoom=0.08,
                    box_alignment=(0.5, 1.0),
                    xycoords=ax.get_xaxis_transform(),  # X em data do eixo, Y em fração
                )

            ax.set_title("Distribuição das notas por jogo")

            ax.yaxis.grid(True, linestyle="--", alpha=0.25)

            plt.tight_layout()
            st.pyplot(fig, width='stretch')
            plt.close(fig)

            idx_jogo_max = notas_por_jogo["Média"].idxmax()
            idx_jogo_min = notas_por_jogo["Média"].idxmin()

            maior_nota = notas_por_jogo["Média"].max()
            menor_nota = notas_por_jogo["Média"].min()

            time_maior_nota = notas_por_jogo.iloc[idx_jogo_max]['VS']
            time_menor_nota = notas_por_jogo.iloc[idx_jogo_min]['VS']

            local_maior_nota = notas_por_jogo.iloc[idx_jogo_max]['Local']
            local_menor_nota = notas_por_jogo.iloc[idx_jogo_min]['Local']

            competicao_maior_nota = notas_por_jogo.iloc[idx_jogo_max]['Competição']
            competicao_menor_nota = notas_por_jogo.iloc[idx_jogo_min]['Competição']

            jogo_maior_nota_str = 'Flamengo x ' + time_maior_nota if local_maior_nota == 'C' else time_maior_nota + ' x Flamengo'
            jogo_menor_nota_str = 'Flamengo x ' + time_menor_nota if local_menor_nota == 'C' else time_menor_nota + ' x Flamengo'

            best_game_col, worst_game_col = st.columns(2)
            best_game_col.markdown(
                "<span style='font-size: 2.5rem;text-align: center;'><b>Melhor jogo</b></span>",
                unsafe_allow_html=True,
                text_alignment='center'
            )
            best_game_col.markdown(
                "<span style='font-size: 2rem;text-align: center;'>" + jogo_maior_nota_str + "</span><br>"
                "<span style='font-size: 1.75rem;text-align: center;'>" + competicao_maior_nota + "</span>",
                unsafe_allow_html=True,
                text_alignment='center'
            )
            best_game_col.markdown(
                "Nota média<br><span style='font-size: 4rem;text-align: center;'>" + str(maior_nota) + "</span>",
                unsafe_allow_html=True,
                text_alignment='center'
            )

            worst_game_col.markdown(
                "<span style='font-size: 2.5rem;text-align: center;'><b>Pior jogo</b></span>",
                unsafe_allow_html=True,
                text_alignment='center'
            )
            worst_game_col.markdown(
                "<span style='font-size: 2rem;text-align: center;'>" + jogo_menor_nota_str + "</span><br>"
                "<span style='font-size: 1.75rem;text-align: center;'>" + competicao_menor_nota + "</span>",
                unsafe_allow_html=True,
                text_alignment='center'
            )
            worst_game_col.markdown(
                "Nota média<br><span style='font-size: 4rem;text-align: center; margin:0'>" + str(menor_nota) + "</span>",
                unsafe_allow_html=True,
                text_alignment='center'
            )

    else:
        st.markdown('Poxa, parece que seus filtros não retornaram nenhum jogo :disappointed: <br>'
                 'Tente refazer ou limpar os filtros', unsafe_allow_html=True)

with tab_jogador:
    selected_jogador_option = st.selectbox(
        "Selecione um jogador",
        [''] + sorted(jogadores_df.Jogador),
    )
    if selected_jogador_option:
        selected_jogador_dict = jogadores_df[jogadores_df['Jogador'] == selected_jogador_option].iloc[0].to_dict()
        jogos_jogador = jogos_df[jogos_df['Jogador'] == selected_jogador_dict['Jogador']]

        if selected_ano:
            jogos_jogador = jogos_jogador[jogos_jogador['Data (Ano)'].isin(selected_ano)]

        if not show_notas_simoes:
            jogos_jogador = jogos_jogador[jogos_jogador['Nota por'] != 'Simões']

        if not show_notas_b10:
            jogos_jogador = jogos_jogador[jogos_jogador['Nota por'] != 'B10']

        if siglas:
            jogos_jogador = jogos_jogador[jogos_jogador['Competição'].isin(siglas)]

        show_charts = True
        if not selected_ano or not siglas or (not show_notas_simoes and not show_notas_b10):
            jogos_jogador = pd.DataFrame()
            show_charts = False

        if len(jogos_jogador) > 0:
            max_nota = jogos_jogador['Nota'].max()
            min_nota = jogos_jogador['Nota'].min()

            jogos_max_df = jogos_jogador[jogos_jogador['Nota'] == max_nota]
            jogos_min_df = jogos_jogador[jogos_jogador['Nota'] == min_nota]

            jogos_max = list_jogos(jogos_max_df, competicoes_df)
            jogos_max_str = '<br>'.join(jogos_max)

            jogos_min = list_jogos(jogos_min_df, competicoes_df)
            jogos_min_str = '<br>'.join(jogos_min)

            qtd_max_nota = len(jogos_jogador[jogos_jogador['Nota'] == max_nota]['Data'].unique())
            qtd_min_nota = len(jogos_jogador[jogos_jogador['Nota'] == min_nota]['Data'].unique())

            max_qtd_str = '' if qtd_max_nota <= 1 else ' (' + str(qtd_max_nota) + 'x)'
            min_qtd_str = '' if qtd_min_nota <= 1 else ' (' + str(qtd_min_nota) + 'x)'
        else:
            max_nota = '-'
            min_nota = '-'

            max_qtd_str = ''
            min_qtd_str = ''

            jogos_max_str = ''
            jogos_min_str = ''


        # CONTAINER COM AS INFORMAÇÕES DO JOGADOR
        container_jogador = st.container()
        jogador_info, jogador_image = container_jogador.columns([0.7, 0.3])
        jogador_info.write('#### ' + selected_jogador_dict['Jogador'])
        jogador_info.write('###### ' + 'Posição: ' + selected_jogador_dict['Posição'])
        with jogador_info.popover('###### ' + 'Maior Nota: ' + str(max_nota) + max_qtd_str):
            st.markdown(jogos_max_str, unsafe_allow_html=True)
        with jogador_info.popover('###### ' + 'Menor Nota: ' + str(min_nota) + min_qtd_str):
            st.markdown(jogos_min_str, unsafe_allow_html=True)
        jogador_image.image(selected_jogador_dict['Image Link'], width="stretch")

        # APRESENTAÇÃO DOS DADOS
        st.subheader('Notas por jogo')
        # st.write(jogos_jogador['Data'].value_counts())
        # st.dataframe(jogos_jogador)
        with st.expander("Tabela de jogos"):
            if len(jogos_jogador) > 0:
                notas_jogador = jogos_jogador.pivot_table(
                        index=["Data", "Competição", "VS", "Local"],
                        columns="Nota por",
                        values="Nota",
                        aggfunc="first"   # ou 'mean' se houver duplicata
                    ).reset_index().rename(
                        columns={
                            "Simões": "Nota Simões",
                            "B10": "Nota B10"
                        }
                    )

                notas_jogador['Competição'] = notas_jogador['Competição'].map(competicoes_df.set_index('Sigla')['Competição'])

                st.dataframe(
                    notas_jogador,
                    hide_index=True
                )

        if len(jogos_jogador) > 0:

            # GRÁFICO SEM A FOTO DO SIMAS E B10
            # x = jogos_jogador['Data'].unique()
            #
            # escudos = get_escudos(jogos_jogador, x, times_dict)
            #
            # fig, ax = plt.subplots(figsize=(6, 4), dpi=200)
            # if show_notas_b10:
            #     y_b10 = notas_por_pessoa(jogos_jogador, 'B10', x)
            #     ax.scatter(x, y_b10, c='black', s=150, alpha=0.5)
            # if show_notas_simoes:
            #     y_simoes = notas_por_pessoa(jogos_jogador, 'Simões', x)
            #     ax.scatter(x, y_simoes, c='red', s=150, alpha=0.5)
            #
            # # remove texto dos ticks
            # ax.set_xticks(x)
            # ax.set_xticklabels([""] * len(x))
            # ax.set_ylim(0, 10)
            #
            # def add_image(ax, img_path, xy, zoom=0.08):
            #     if not os.path.exists(img_path):
            #         return  # evita crash se faltar imagem
            #     img = mpimg.imread(img_path)
            #     imagebox = OffsetImage(img, zoom=zoom)
            #     ab = AnnotationBbox(
            #         imagebox,
            #         xy,
            #         frameon=False,
            #         box_alignment=(0.5, 1.1)
            #     )
            #     ax.add_artist(ab)
            #
            #
            # # adiciona imagens no eixo X
            # y_min = ax.get_ylim()[0]
            # for xi, img_path in zip(x, escudos):
            #     add_image(ax, img_path, (xi, y_min))
            #
            # ax.set_ylabel("Nota")
            # ax.set_title("Jogos do " + selected_jogador_dict['Jogador'])
            #
            # plt.tight_layout()
            # st.pyplot(fig, use_container_width=True)
            # plt.close(fig)

            # GRÁFICO COM FOTOS

            x = sorted(jogos_jogador["Data"].unique())
            escudos = get_escudos(jogos_jogador, x, times_dict)

            foto_b10 = "media/canal/b10.png"
            foto_simoes = "media/canal/simoes.png"

            fig, ax = plt.subplots(figsize=(6, 4), dpi=200)

            DX = 4  # deslocamento em pixels quando sobreposto
            Y_EPS = 0.05  # tolerância de sobreposição (ajuste: 0.1 se quiser mais sensível)

            def is_missing(v):
                return v is None or (isinstance(v, float) and math.isnan(v))

            # --- Pega as notas (sempre cria listas do mesmo tamanho) ---
            y_b10 = notas_por_pessoa(jogos_jogador, "B10", x) if show_notas_b10 else [None] * len(x)
            y_simoes = notas_por_pessoa(jogos_jogador, "Simões", x) if show_notas_simoes else [None] * len(x)

            # --- Scatter base (opcional) ---
            if show_notas_b10:
                ax.scatter(x, y_b10, c="black", s=150, alpha=0.25)
            if show_notas_simoes:
                ax.scatter(x, y_simoes, c="red", s=150, alpha=0.25)

            # --- Fotos nos pontos: offset só quando sobrepostos ---
            for xi, y1, y2 in zip(x, y_b10, y_simoes):
                overlap = (not is_missing(y1)) and (not is_missing(y2)) and (abs(y1 - y2) <= Y_EPS)

                off_b10 = (-DX, 0) if overlap else (0, 0)
                off_simoes = (DX, 0) if overlap else (0, 0)

                if show_notas_b10 and not is_missing(y1):
                    add_image(ax, foto_b10, (xi, y1), zoom=0.07, xybox=off_b10)

                if show_notas_simoes and not is_missing(y2):
                    add_image(ax, foto_simoes, (xi, y2), zoom=0.07, xybox=off_simoes)

            # --- Eixo X com escudos (sem offset) ---
            ax.set_xticks(x)
            ax.set_xticklabels([""] * len(x))
            ax.set_ylim(0, 10)
            ax.set_yticks(range(0, 11, 1))
            # grid suave
            ax.yaxis.grid(True, linestyle="--", alpha=0.25)
            ax.xaxis.grid(False)

            # fundo levemente acinzentado
            ax.set_facecolor("#e6e6e6")
            fig.patch.set_facecolor("#e6e6e6")

            # remove bordas
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            def add_shield(ax, img_path, x_value, y_value, zoom=0.08):
                if not img_path or not os.path.exists(img_path):
                    return
                img = mpimg.imread(img_path)
                imagebox = OffsetImage(img, zoom=zoom)
                ab = AnnotationBbox(
                    imagebox,
                    (x_value, y_value),
                    frameon=False,
                    box_alignment=(0.5, 1.1),
                    clip_on=False
                )
                ax.add_artist(ab)


            y_min = ax.get_ylim()[0]
            for xi, escudo_path in zip(x, escudos):
                add_shield(ax, escudo_path, xi, y_min, zoom=0.08)

            ax.set_ylabel("Nota")
            ax.set_title("Jogos do " + selected_jogador_dict["Jogador"])

            plt.tight_layout()
            st.pyplot(fig, width='stretch')
            plt.close(fig)

            st.subheader('Desempenho por competição')
            # st.dataframe(jogos_jogador)
            competicoes_jogadas = jogos_jogador['Competição'].unique()
            n_columns_compet = 3
            for id_row, row in enumerate(split_list(competicoes_jogadas, n_columns_compet)):
                notas_competicao_cols = st.columns(n_columns_compet)
                for idx, logo in enumerate(row):

                    id_nota = idx + n_columns_compet*id_row

                    notas_competicao_cols[idx].markdown(
                        "<span style='font-size: 2rem;text-align: center;'><b>" + competicao_dict[competicoes_jogadas[id_nota]][
                            'name'] + "</b></span>",
                        unsafe_allow_html=True,
                        text_alignment='center'
                    )
                    nota_media = jogos_jogador[jogos_jogador['Competição'] == competicoes_jogadas[id_nota]]['Nota'].mean()
                    notas_competicao_cols[idx].markdown(
                        "<span style='font-size: 4rem;text-align: center;'>" + str(round(nota_media, 1)) + "</span>",
                        unsafe_allow_html=True,
                        text_alignment='center'
                    )

