import pandas as pd
# import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# MODO PANTALLA COMPLETA
st.set_page_config(layout="wide")
# MARKDOWN PARA AUMENTAR FUENTE
st.markdown("""
<style>
.big-font {
    font-size:20px !important;
}
</style>
""", unsafe_allow_html=True)

# CARGA ARCHIVOS
GastosGrupos = pd.read_csv("GastosGrupos.csv", sep=';')
GastosHistorico = pd.read_csv("GastosHistorico.csv", sep=';')
# Merge Archivos
GastosAll = pd.merge(GastosHistorico, GastosGrupos, how='left')
GastosAll.sort_values(by=['ID_Mes', 'Grupo'], inplace=True)
GastosAll['Fecha'] = pd.to_datetime(GastosAll['Fecha'], format="%d/%m/%Y")
#st.write(GastosAll)

st.sidebar.title('Menú Principal')
opcion = st.sidebar.radio('Opciones:', ['Ver Datos Históricos', 'Ver Detalle Mensual','Buscar concepto'])

if opcion == 'Ver Datos Históricos':
    st.title('Histórico de Gastos')
    # EVOLUCIÓN MENSUAL
    # Generar Tabla Dinámica
    GHist = pd.pivot_table(GastosAll, index=['Grupo'], columns='ID_Mes', values='Importe', aggfunc=sum, fill_value=0)
    GHist.columns = pd.unique(GastosAll['Mes'])

    # Crear Gráfica asociada
    fig = go.Figure()
    # listval = GHist.index.values.tolist()[::-1]
    for idx in GHist.index:
        if idx != GHist.index[-1]:
            fig.add_trace(go.Bar(name=idx, x=GHist.columns, y=list(GHist.loc[idx, :])))
        else:
            # En la última categoría, añadimos la anotación de la suma total
            fig.add_trace(go.Bar(name=idx, x=GHist.columns, y=list(GHist.loc[idx, :]), texttemplate=['{val:.0f}€'
                                 .format(val=GHist.sum()[i]) for i in range(len(GHist.sum()))], textposition='outside'))
    fig.update_layout(barmode='stack')
    fig.update_layout(height=700)
    fig.update_xaxes(title_text='Mes')
    fig.update_yaxes(title_text='Gasto (€)')

    # Header + Subheader + Gráfica + Tabla
    st.header('Histórico Mensual')
    st.subheader('Comparativa Mensual')
    st.plotly_chart(fig, use_container_width=True)
    st.subheader('Tabla Resumen')
    GHist.loc['TOTAL'] = GHist.sum()  # Añadimos el total a la tabla
    st.table(GHist.T)

    # DISTRIBUCIÓN GASTO ACUMULADO
    # Creación Gráfica asociada
    fig2 = px.treemap(GastosAll.sort_values(by=['Importe']), path=['Grupo', 'Categoria'], color='Grupo',
                      values='Importe')
    fig2.update_traces(textinfo='label+percent entry')
    fig2.update_traces(hovertemplate='<b>%{label} </b><br> id: %{currentPath}%{label} <br> Importe: %{value:.0f}€<br> '
                                     'Porcentaje relativo: %{percentEntry:.1%} <br>Porcentaje absoluto:'
                                     ' %{percentRoot:.1%}')
    fig2.update_layout(height=700)
    # Header + Subheader + Gráfica
    st.header('Distribución del gasto acumulado')
    st.plotly_chart(fig2, use_container_width=True)

    #  GASTO PROMEDIO
    st.header('Promedio mensual de gasto')
    media = GastosAll['Importe'].sum() / GastosAll['ID_Mes'].max()
    st.markdown('<p class="big-font"> El promedio mensual de gastos asciende a  <strong>{media:.0f}€</strong>, que se'
                ' desglosan de la siguiente forma: </p>'.format(media=media), unsafe_allow_html=True)
    GHistProm = GHist.iloc[:-1, :].T.mean()
    c1, c2 = st.columns((0.5, 0.5))
    fig3 = px.bar(GHistProm, x=[0], y=GHistProm.index, color=GHistProm.index)
    fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
    fig3.update_xaxes(title_text='Gasto Promedio(€)')
    fig3.update_layout(height=700)
    c1.write('Por grupo')
    c1.plotly_chart(fig3, use_container_width=True)
    GHistProm = pd.DataFrame(GHistProm.reset_index())
    GHistProm.columns = ['Grupo', 'Gasto Promedio (€)']
    c1.table(GHistProm)
    GHistCatProm = pd.pivot_table(GastosAll, index=['Grupo', 'Categoria'], columns='ID_Mes', values='Importe',
                                  aggfunc=sum, fill_value=0).T.mean().reset_index()
    fig4 = px.bar(GHistCatProm, x=[0], y='Categoria', color='Grupo')
    fig4.update_layout(yaxis={'categoryorder': 'total ascending'})
    fig4.update_xaxes(title_text='Gasto Promedio(€)')
    fig4.update_layout(height=700)
    c2.write('Por categoria')
    c2.plotly_chart(fig4, use_container_width=True)
    GHistCatProm = pd.DataFrame(GHistCatProm)
    GHistCatProm.columns = ['Grupo', 'Categoria', 'Gasto Promedio (€)']
    c2.table(GHistCatProm)
elif opcion == 'Ver Detalle Mensual':
    mes = st.sidebar.selectbox('Selecciona el mes:', pd.unique(GastosAll['Mes'])[::-1], 0)
    mesind = list(pd.unique(GastosAll['Mes'])).index(mes) + 1
    st.title('Detalle de gasto mensual')
    if mesind == 1:
        ant = False
        GastMes = GastosAll[GastosAll['ID_Mes'] == mesind].copy()
        tot = GastMes['Importe'].sum()
    else:
        ant = True
        GastMes = GastosAll[GastosAll['ID_Mes'].isin([mesind, mesind - 1])].copy()
        tot = GastMes[GastMes['ID_Mes'] == mesind]['Importe'].sum()
        difant = tot - GastMes[GastMes['ID_Mes'] == mesind - 1]['Importe'].sum()

    st.header('Puntos clave')
    st.markdown('<p class="big-font"> Los gastos de {mes} ascienden a  <strong>{val:.0f}€. </p>'
                .format(mes=mes, val=tot), unsafe_allow_html=True)
    if ant:
        st.markdown("<ul><li>Respecto a {mesant}, la diferencia es de {sig}{dif:.0f}€.</li></ul> </p>"
                    .format(mesant=list(pd.unique(GastosAll['Mes']))[mesind-2], sig=['+' if difant > 0 else ""][0],
                            dif=difant), unsafe_allow_html=True)
    st.markdown("<ul><li>Respecto a los ingresos, suponen {sig}{dif:.0f}€.</li></ul> </p>"
                .format(sig=['un ahorro de +' if 1960-tot > 0 else 'un exceso de gasto de '][0],
                        dif=abs(tot-1960)), unsafe_allow_html=True)

    # st.markdown("<ul> <li>a</li> <li>ab</li></ul>",unsafe_allow_html=True)

    # DISTRIBUCIÓN GASTO ACUMULADO
    # Creación Gráfica asociada
    fig5 = px.sunburst(GastMes[GastMes['ID_Mes'] == mesind].sort_values(by=['Importe']), path=['Grupo', 'Categoria'],
                       color='Grupo', values='Importe')
    fig5.update_traces(textinfo='label+percent entry')
    fig5.update_traces(hovertemplate='<b>%{label} </b><br> id: %{currentPath}%{label} <br> Importe: %{value:.0f}€<br> '
                                     'Porcentaje relativo: %{percentEntry:.1%} <br>Porcentaje absoluto:'
                                     ' %{percentRoot:.1%}')
    fig5.update_layout(height=700)
    # Header + Subheader + Gráfica
    st.header('Distribución del gasto en {mes}'.format(mes=mes))
    st.plotly_chart(fig5, use_container_width=True)
    
    st.header('Desglose de gasto en {mes}'.format(mes=mes))
    st.subheader('Por grupo')
    GMesDes = pd.pivot_table(GastMes, index=['Grupo'], columns='ID_Mes', values='Importe', aggfunc=sum, fill_value=0)
    if ant:
        GMesDes['Dif. Mes Ant.'] = GMesDes[mesind]-GMesDes[mesind-1]
        GMesDes.columns = [list(pd.unique(GastosAll['Mes']))[mesind-2], mes, 'Dif. Mes Ant.']
        GMesDes.drop(columns=[list(pd.unique(GastosAll['Mes']))[mesind-2]], inplace=True)
        GMesDes.reset_index(inplace=True)
    else:
        GMesDes.columns = [mes]
        GMesDes.reset_index(inplace=True)

    fig7 = px.bar(GMesDes, x=mes, y='Grupo', color='Grupo')
    fig7.update_layout(yaxis={'categoryorder': 'total ascending'})
    fig7.update_xaxes(title_text='Gasto (€)')
    fig7.update_layout(height=700)

    c1, c2 = st.columns((0.6, 0.4))
    if not ant:
        st.plotly_chart(fig7, use_container_width=True)
        st.table(GMesDes)
    else:
        color_val = ["green" if val <= 0 else "red" for val in GMesDes['Dif. Mes Ant.']]
        fig8 = px.bar(GMesDes, x='Dif. Mes Ant.', y='Grupo', color='Grupo', color_discrete_sequence=color_val)
        fig8.update_layout(yaxis={'categoryorder': 'total descending'})
        fig8.update_xaxes(title_text='Diferencia gasto respecto a {mesant}'
                                     ' (€)'.format(mesant=list(pd.unique(GastosAll['Mes']))[mesind-2]))
        fig8.update_layout(height=700)
        fig8.layout.update(showlegend=False)

        c1.plotly_chart(fig7, use_container_width=True)
        c2.plotly_chart(fig8, use_container_width=True)
        st.table(GMesDes)
    # -----------------------------------------------------------
    st.subheader("Por categoría")
    GMesCat = pd.pivot_table(GastMes, index=['Grupo','Categoria'], columns='ID_Mes', values='Importe', aggfunc=sum, fill_value=0)
    if ant:
        GMesCat['Dif. Mes Ant.'] = GMesCat[mesind] - GMesCat[mesind - 1]
        GMesCat.columns = [list(pd.unique(GastosAll['Mes']))[mesind - 2], mes, 'Dif. Mes Ant.']
        GMesCat.drop(columns=[list(pd.unique(GastosAll['Mes']))[mesind - 2]], inplace=True)
        GMesCat.reset_index(inplace=True)
    else:
        GMesCat.columns = [mes]
        GMesCat.reset_index(inplace=True)

    fig9 = px.bar(GMesCat[GMesCat[mes] != 0], x=mes, y='Categoria', color='Grupo')
    fig9.update_layout(yaxis={'categoryorder': 'total ascending'})
    fig9.update_xaxes(title_text='Gasto (€)')
    fig9.update_layout(height=700)

    c1, c2 = st.columns((0.6, 0.4))
    if not ant:
        st.plotly_chart(fig9, use_container_width=True)
        st.table(GMesCat)
    else:
        val = [val for val in GMesCat['Dif. Mes Ant.']]
        color_val = ["green" if val <= 0 else "red" for val in GMesCat['Dif. Mes Ant.']]
        fig10 = px.bar(GMesCat, x='Dif. Mes Ant.', y='Categoria', color='Categoria', color_discrete_sequence=color_val)
        fig10.update_layout(yaxis={'categoryorder': 'total descending'})
        fig10.update_xaxes(title_text='Diferencia gasto respecto a {mesant} '                                      '(€)'.format(mesant=list(pd.unique(GastosAll['Mes']))[mesind - 2]))
        fig10.update_layout(height=700)
        fig10.layout.update(showlegend=False)

        c1.plotly_chart(fig9, use_container_width=True)
        c2.plotly_chart(fig10, use_container_width=True)
    st.table(GMesCat)

    st.header('Evolución Temporal del Gasto')
    GastMes = GastMes[GastMes['Mes'] == mes]
    fig11 = px.bar(GastMes, x='Fecha', y='Importe', color='Grupo')
    fig11.update_layout(height=700)
    fig11.update_xaxes(tickangle=-45, tickmode='linear')
    st.plotly_chart(fig11, use_container_width=True)

    st.header('Extracto')
    st.write(GastMes)

else:
    st.header('Desglose de Concepto')
    grupo = st.selectbox('Escoge un grupo:', pd.unique(GastosAll['Grupo']))
    GastosAll = GastosAll[GastosAll['Grupo'] == grupo]
    concepto = st.multiselect('Escoge un concepto para ver en detalle:', sorted(list(pd.unique(GastosAll['Concepto']))))
    GastosAll = GastosAll[GastosAll['Concepto'] .isin(concepto)]
    fig = px.bar(GastosAll.reset_index(), x='Mes', y='Importe',color='Concepto')
    fig.update_layout(height=700)
    st.subheader('Gráfica asociada')
    st.plotly_chart(fig, use_container_width=True)
    st.subheader('Extracto asociado')
    st.write(GastosAll)


