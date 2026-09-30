import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
from flask import Flask, render_template, request
import sqlite3
import logging

app = Flask(__name__)

# Configuração de Logging
logging.basicConfig(level=logging.DEBUG)


# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect(
        'contratos_publicos.db')  # Substitua 'database.db' pelo nome do seu arquivo de banco de dados
    conn.row_factory = sqlite3.Row  # Permite acessar os dados como dicionários
    return conn


@app.route('/')
def index():
    # Conexão com o banco de dados
    conn = get_db_connection()

    # Consulta para buscar os contratos
    contratos = conn.execute('SELECT id, objeto_contrato FROM contratos').fetchall()

    # Fecha a conexão
    conn.close()

    # Passa os contratos para o template
    return render_template('index.html', contratos=contratos)


# Rota de pesquisa
@app.route('/pesquisar')
def pesquisar():
    try:
        id_contrato = request.args.get('id_contrato')
        logging.debug(f"ID do contrato pesquisado: {id_contrato}")

        if not id_contrato:
            raise ValueError("O ID do contrato não foi fornecido.")

        conn = get_db_connection()
        contrato = conn.execute('''
            SELECT c.id, c.tipo_procedimento, c.preco, c.objeto_contrato, c.prazo_execucao, c.procedimento_centralizado, c.adjudicante,
                aq.descr_acordo_quadro,
                a.designacao as designacao, a.tipo_juridico as tipo_juridico,
                dc.dia as dia_celebracao, dc.mes as mes_celebracao, dc.ano as ano_celebracao,
                dp.dia as dia_publicacao, dp.mes as mes_publicacao, dp.ano as ano_publicacao,
                f.fundamentacao
            FROM contratos c
            JOIN acordo_quadro aq ON c.id = aq.id_contrato
            JOIN data_celebracao dc ON c.id = dc.id
            JOIN data_publicacao dp ON c.id = dp.id
            JOIN fundamentacao f ON c.id = f.id
            JOIN adjudicantes a ON c.adjudicante = a.nif

            WHERE c.id = ?
        ''', (id_contrato,)).fetchone()

        cpvs = conn.execute('''
            SELECT cc.cpv_id as cpv_id, cpv.descricao as descricao
            FROM cpv_contratos cc
            JOIN cpv ON cc.cpv_id = cpv.cpv_id
            WHERE cc.contrato = ?
        ''', (id_contrato,)).fetchall()

        # Concatenate CPVs into a single string separated by 'enter'
        cpvs_list = [f"{cpv['cpv_id']} : {cpv['descricao']}" for cpv in cpvs]
        cpvs_str = '<br>'.join(cpvs_list)

        adjus = conn.execute('''
            SELECT a.nif as nif, a.designacao as designacao, a.tipo_juridico as tipo_juridico
            FROM adjudicatarios_contratos ac
            JOIN adjudicatarios a ON ac.nif = a.nif
            WHERE ac.id = ?
        ''', (id_contrato,)).fetchall()

        # Concatenate Adjudicatarios into a single string separated by 'enter'
        adju_list = [f"{adju['nif']} | {adju['designacao']} | {adju['tipo_juridico']}" for adju in adjus]
        adju_str = '<br>'.join(adju_list)

        locs = conn.execute('''
            SELECT l.pais as pais, l.distrito as distrito, l.concelho as concelho
            FROM locais_contratos lc
            JOIN locais l ON lc.cod_local = l.cod_local
            WHERE lc.contratos = ?
        ''', (id_contrato,)).fetchall()

        # Concatenate Adjudicatarios into a single string separated by 'enter'
        loc_list = [f"{loc['pais']}, {loc['distrito']}, {loc['concelho']}" for loc in locs]
        loc_str = '<br>'.join(loc_list)

        tcs = conn.execute('''
            SELECT tc.tipo as tipo
            FROM tipocontr_contratos tcc
            JOIN tipo_contratos tc ON tcc.linha_num = tc.linha_num
            WHERE tcc.id = ?
        ''', (id_contrato,)).fetchall()

        # Concatenate Adjudicatarios into a single string separated by 'enter'
        tc_list = [f"{tc['tipo']}" for tc in tcs]
        tc_str = '<br>'.join(tc_list)

        conn.close()

        logging.debug(f"Contrato encontrado: {contrato}")
        logging.debug(f"CPVs encontrados: {cpvs_str}")
        logging.debug(f"Adjudicatários encontrados: {adju_str}")
        logging.debug(f"Locais encontrados: {loc_str}")
        logging.debug(f"Tipos de Contratos encontrados: {tc_str}")
        return render_template('resultado_pesquisa.html', contrato=contrato, cpvs_str=cpvs_str, adju_str=adju_str,
                               loc_str=loc_str, tc_str=tc_str)

    except Exception as e:
        logging.error(f"Erro ao pesquisar contratos: {e}")
        return render_template('erro.html', mensagem=f"Erro ao pesquisar contratos: {e}")


@app.route('/pesquisar-objeto', methods=['GET'])
def pesquisar_objeto():
    objeto_contrato = request.args.get('objeto_contrato', '').strip()  # Obtém o termo da pesquisa
    conn = get_db_connection()

    # Pesquisa no banco de dados por objeto_contrato
    query = "SELECT id, objeto_contrato FROM contratos WHERE objeto_contrato LIKE ?"
    resultados = conn.execute(query, (f"%{objeto_contrato}%",)).fetchall()
    conn.close()

    # Renderiza a mesma página com os resultados da pesquisa
    return render_template('index.html', contratos=resultados)


@app.route('/pesquisar-objeto', methods=['GET'])
def pesquisar_id():
    id = request.args.get('id', '').strip()  # Obtém o termo da pesquisa
    conn = get_db_connection()

    # Pesquisa no banco de dados por objeto_contrato
    query = "SELECT id, objeto_contrato FROM contratos WHERE id LIKE ?"
    resultados = conn.execute(query, (f"%{id}%",)).fetchall()
    conn.close()

    # Renderiza a mesma página com os resultados da pesquisa
    return render_template('index.html', contratos=resultados)


@app.route('/detalhes/<int:id>', methods=['GET'])
def detalhes(id):
    try:
        conn = get_db_connection()
        contrato = conn.execute('''
                    SELECT c.id, c.tipo_procedimento, c.preco, c.objeto_contrato, c.prazo_execucao, c.procedimento_centralizado, c.adjudicante,
                        aq.descr_acordo_quadro,
                        a.designacao as designacao, a.tipo_juridico as tipo_juridico,
                        dc.dia as dia_celebracao, dc.mes as mes_celebracao, dc.ano as ano_celebracao,
                        dp.dia as dia_publicacao, dp.mes as mes_publicacao, dp.ano as ano_publicacao,
                        f.fundamentacao
                    FROM contratos c
                    JOIN acordo_quadro aq ON c.id = aq.id_contrato
                    JOIN data_celebracao dc ON c.id = dc.id
                    JOIN data_publicacao dp ON c.id = dp.id
                    JOIN fundamentacao f ON c.id = f.id
                    JOIN adjudicantes a ON c.adjudicante = a.nif

                    WHERE c.id = ?
                ''', (id,)).fetchone()

        cpvs = conn.execute('''
                    SELECT cc.cpv_id as cpv_id, cpv.descricao as descricao
                    FROM cpv_contratos cc
                    JOIN cpv ON cc.cpv_id = cpv.cpv_id
                    WHERE cc.contrato = ?
                ''', (id,)).fetchall()

        # Concatenate CPVs into a single string separated by 'enter'
        cpvs_list = [f"{cpv['cpv_id']} : {cpv['descricao']}" for cpv in cpvs]
        cpvs_str = '<br>'.join(cpvs_list)

        adjus = conn.execute('''
                    SELECT a.nif as nif, a.designacao as designacao, a.tipo_juridico as tipo_juridico
                    FROM adjudicatarios_contratos ac
                    JOIN adjudicatarios a ON ac.nif = a.nif
                    WHERE ac.id = ?
                ''', (id,)).fetchall()

        # Concatenate Adjudicatarios into a single string separated by 'enter'
        adju_list = [f"{adju['nif']} : {adju['designacao']} , {adju['tipo_juridico']}" for adju in adjus]
        adju_str = '<br>'.join(adju_list)

        locs = conn.execute('''
                    SELECT l.pais as pais, l.distrito as distrito, l.concelho as concelho
                    FROM locais_contratos lc
                    JOIN locais l ON lc.cod_local = l.cod_local
                    WHERE lc.contratos = ?
                ''', (id,)).fetchall()

        # Concatenate Adjudicatarios into a single string separated by 'enter'
        loc_list = [f"{loc['pais']}, {loc['distrito']}, {loc['concelho']}" for loc in locs]
        loc_str = '<br>'.join(loc_list)

        tcs = conn.execute('''
                    SELECT tc.tipo as tipo
                    FROM tipocontr_contratos tcc
                    JOIN tipo_contratos tc ON tcc.linha_num = tc.linha_num
                    WHERE tcc.id = ?
                ''', (id,)).fetchall()

        # Concatenate Adjudicatarios into a single string separated by 'enter'
        tc_list = [f"{tc['tipo']}" for tc in tcs]
        tc_str = '<br>'.join(tc_list)

        conn.close()

        logging.debug(f"Contrato encontrado: {contrato}")
        logging.debug(f"CPVs encontrados: {cpvs_str}")
        logging.debug(f"Adjudicatários encontrados: {adju_str}")
        logging.debug(f"Locais encontrados: {loc_str}")
        logging.debug(f"Tipos de Contratos encontrados: {tc_str}")
        return render_template('resultado_pesquisa.html', contrato=contrato, cpvs_str=cpvs_str, adju_str=adju_str,
                               loc_str=loc_str, tc_str=tc_str)

    except Exception as e:
        logging.error(f"Erro ao pesquisar contratos: {e}")
        return render_template('erro.html', mensagem=f"Erro ao pesquisar contratos: {e}")


@app.route('/entidades')
def entidades():
    return render_template('entidades.html')  # Um novo template para a página de entidades


@app.route('/adjudicantes', methods=['GET', 'POST'])
def adjudicantes():
    conn = get_db_connection()

    # Se o usuário realizar uma pesquisa
    nif_pesquisado = request.form.get('nif', '').strip()
    if nif_pesquisado:
        query = '''
        SELECT 
            a.nif, 
            a.designacao, 
            a.tipo_juridico, 
            GROUP_CONCAT(c.id, ',') AS contratos
        FROM 
            adjudicantes a
        LEFT JOIN 
            contratos c 
        ON 
            a.nif = c.adjudicante
        WHERE 
            a.nif LIKE ?
        GROUP BY 
            a.nif, a.designacao, a.tipo_juridico
        '''
        # Pesquisar pelo NIF
        adjudicantes = conn.execute(query, (f"%{nif_pesquisado}%",)).fetchall()
    else:
        query = '''
        SELECT 
            a.nif, 
            a.designacao, 
            a.tipo_juridico, 
            GROUP_CONCAT(c.id, ',') AS contratos
        FROM 
            adjudicantes a
        LEFT JOIN 
            contratos c 
        ON 
            a.nif = c.adjudicante
        GROUP BY 
            a.nif, a.designacao, a.tipo_juridico
        '''
        # Se não for feita uma pesquisa, retorna todos os adjudicantes
        adjudicantes = conn.execute(query).fetchall()

    conn.close()

    # Passando as variáveis para o template
    return render_template('adjudicantes.html', adjudicantes=adjudicantes, nif_pesquisado=nif_pesquisado)


@app.route('/resultados_pesquisa/<int:id>', methods=['GET'])
def resultados_pesquisa(id):
    # Conecte-se ao banco de dados
    conn = get_db_connection()

    # Realize a consulta para obter os detalhes do contrato com base no id
    contrato = conn.execute('''
                        SELECT c.id, c.tipo_procedimento, c.preco, c.objeto_contrato, c.prazo_execucao, c.procedimento_centralizado, c.adjudicante,
                            aq.descr_acordo_quadro,
                            a.designacao as designacao, a.tipo_juridico as tipo_juridico,
                            dc.dia as dia_celebracao, dc.mes as mes_celebracao, dc.ano as ano_celebracao,
                            dp.dia as dia_publicacao, dp.mes as mes_publicacao, dp.ano as ano_publicacao,
                            f.fundamentacao
                        FROM contratos c
                        JOIN acordo_quadro aq ON c.id = aq.id_contrato
                        JOIN data_celebracao dc ON c.id = dc.id
                        JOIN data_publicacao dp ON c.id = dp.id
                        JOIN fundamentacao f ON c.id = f.id
                        JOIN adjudicantes a ON c.adjudicante = a.nif

                        WHERE c.id = ?
                    ''', (id,)).fetchone()

    cpvs = conn.execute('''
                        SELECT cc.cpv_id as cpv_id, cpv.descricao as descricao
                        FROM cpv_contratos cc
                        JOIN cpv ON cc.cpv_id = cpv.cpv_id
                        WHERE cc.contrato LIKE ?
                    ''', (id,)).fetchall()

    # Concatenate CPVs into a single string separated by 'enter'
    cpvs_list = [f"{cpv['cpv_id']} : {cpv['descricao']}" for cpv in cpvs]
    cpvs_str = '<br>'.join(cpvs_list)

    adjus = conn.execute('''
                        SELECT a.nif as nif, a.designacao as designacao, a.tipo_juridico as tipo_juridico
                        FROM adjudicatarios_contratos ac
                        JOIN adjudicatarios a ON ac.nif = a.nif
                        WHERE ac.id = ?
                    ''', (id,)).fetchall()

    # Concatenate Adjudicatarios into a single string separated by 'enter'
    adju_list = [f"{adju['nif']} : {adju['designacao']} , {adju['tipo_juridico']}" for adju in adjus]
    adju_str = '<br>'.join(adju_list)

    locs = conn.execute('''
                        SELECT l.pais as pais, l.distrito as distrito, l.concelho as concelho
                        FROM locais_contratos lc
                        JOIN locais l ON lc.cod_local = l.cod_local
                        WHERE lc.contratos = ?
                    ''', (id,)).fetchall()

    # Concatenate Adjudicatarios into a single string separated by 'enter'
    loc_list = [f"{loc['pais']}, {loc['distrito']}, {loc['concelho']}" for loc in locs]
    loc_str = '<br>'.join(loc_list)

    tcs = conn.execute('''
                        SELECT tc.tipo as tipo
                        FROM tipocontr_contratos tcc
                        JOIN tipo_contratos tc ON tcc.linha_num = tc.linha_num
                        WHERE tcc.id = ?
                    ''', (id,)).fetchall()

    # Concatenate Adjudicatarios into a single string separated by 'enter'
    tc_list = [f"{tc['tipo']}" for tc in tcs]
    tc_str = '<br>'.join(tc_list)



    conn.close()

    if contrato:
        # Renderize a página com os detalhes do contrato
        return render_template('resultado_pesquisa.html', contrato=contrato, cpvs_str=cpvs_str, adju_str=adju_str, loc_str=loc_str, tc_str=tc_str)
    else:
        return "Contrato não encontrado", 404


@app.route('/adjudicatarios', methods=['GET', 'POST'])
def adjudicatarios():
    conn = get_db_connection()
    adjudicatarios = conn.execute(''' 
        SELECT a.nif, a.designacao, a.tipo_juridico, GROUP_CONCAT(ac.id) as ids
        FROM adjudicatarios a
        JOIN adjudicatarios_contratos ac ON a.nif = ac.nif
        GROUP BY a.nif, a.designacao, a.tipo_juridico
    ''').fetchall()

    conn.close()
    return render_template('adjudicatarios.html', adjudicatarios=adjudicatarios)


@app.route("/tipos-de-procedimento", methods=['GET'])
def tipos_de_procedimento():
    tipo_procedimentos = request.args.getlist('tipo_procedimento')
    query = '''
        SELECT id, tipo_procedimento, procedimento_centralizado 
        FROM contratos 
    '''

    if tipo_procedimentos:
        placeholders = ', '.join(['?'] * len(tipo_procedimentos))
        query += f'WHERE tipo_procedimento IN ({placeholders})'

    conn = get_db_connection()
    resultados = conn.execute(query, tipo_procedimentos).fetchall()
    conn.close()

    return render_template("procedimento.html", resultados=resultados)

@app.route('/datas')
def datas():
    return render_template('datas.html')

@app.route('/data_publicacao', methods=['GET', 'POST'])
def data_publicacao():
    conn = get_db_connection()

    # Captura filtros do formulário
    year_filter = request.form.get('year', '').strip()  # Filtro pelo ano
    month_filter = request.form.get('month', '').strip()  # Filtro pelo mês
    day_filter = request.form.get('day', '').strip()  # Filtro pelo dia

    # Consulta inicial sem filtros
    query = "SELECT id, ano, mes, dia FROM data_publicacao"
    params = []

    # Adiciona filtros na consulta
    if year_filter:
        query += " WHERE ano = ?"
        params.append(year_filter)
    if month_filter:
        query += " AND mes = ?" if year_filter else " WHERE mes = ?"
        params.append(month_filter)
    if day_filter:
        query += " AND dia = ?" if year_filter or month_filter else " WHERE dia = ?"
        params.append(day_filter)

    # Executa consulta com os parâmetros
    tabela = conn.execute(query, params).fetchall()
    conn.close()

    # Renderiza a página com os resultados
    return render_template('data_publicacao.html', tabela=tabela, year_filter=year_filter, month_filter=month_filter, day_filter=day_filter)

@app.route('/data_celebracao', methods=['GET', 'POST'])
def data_celebracao():
    conn = get_db_connection()

    # Captura filtros do formulário
    year_filter = request.form.get('year', '').strip()  # Filtro pelo ano
    month_filter = request.form.get('month', '').strip()  # Filtro pelo mês
    day_filter = request.form.get('day', '').strip()  # Filtro pelo dia

    # Consulta inicial sem filtros
    query = "SELECT id, ano, mes, dia FROM data_celebracao"
    params = []

    # Adiciona filtros na consulta
    if year_filter:
        query += " WHERE ano = ?"
        params.append(year_filter)
    if month_filter:
        query += " AND mes = ?" if year_filter else " WHERE mes = ?"
        params.append(month_filter)
    if day_filter:
        query += " AND dia = ?" if year_filter or month_filter else " WHERE dia = ?"
        params.append(day_filter)

    # Executa consulta com os parâmetros
    tabela = conn.execute(query, params).fetchall()
    conn.close()

    # Renderiza a página com os resultados
    return render_template('data_celebracao.html', tabela=tabela, year_filter=year_filter, month_filter=month_filter, day_filter=day_filter)


@app.route("/questoes")
def questoes():
    conn = get_db_connection()
    # Query para a pergunta 1
    pergunta1 = conn.execute('''
        SELECT c.id, MAX(c.preco) as valor_maximo, ad.designacao as adjudicante, adj.designacao as adjudicatario
        FROM contratos c
        JOIN adjudicantes ad ON c.adjudicante = ad.nif
        JOIN adjudicatarios_contratos ac ON c.id = ac.id
        JOIN adjudicatarios adj ON ac.nif = adj.nif
    ''').fetchone()

    # Query para a pergunta 2
    pergunta2 = conn.execute('''
        SELECT l.distrito as distrito, COUNT(lc.cod_local) as contratos
        FROM locais l
        JOIN locais_contratos lc ON l.cod_local = lc.cod_local
        WHERE l.pais = 'Portugal'
        GROUP BY l.distrito
        ORDER BY contratos DESC
        LIMIT 5
    ''').fetchall()

    # Query para a pergunta 3
    pergunta3 = conn.execute('''
        SELECT c.cpv_id, c.descricao, COUNT(cc.contrato) as quantidade_contratos
        FROM cpv c
        JOIN cpv_contratos cc ON c.cpv_id = cc.cpv_id
        GROUP BY c.cpv_id, c.descricao
        ORDER BY quantidade_contratos DESC
        LIMIT 5;
    ''').fetchall()

    # Query para a pergunta 4
    pergunta4 = conn.execute('''
        SELECT adj.designacao AS adjudicante, adt.designacao AS adjudicatario, COUNT(c.id) AS quantidade_contratos
        FROM contratos c
        JOIN adjudicantes adj ON c.adjudicante = adj.nif
        JOIN adjudicatarios_contratos ac ON c.id = ac.id
        JOIN adjudicatarios adt ON ac.nif = adt.nif
        GROUP BY adj.designacao, adt.designacao
        ORDER BY quantidade_contratos DESC
        LIMIT 5;
    ''').fetchall()

    # Query para a pergunta 5
    pergunta5 = conn.execute('''
        SELECT adj.designacao AS adjudicante, ceil(avg(c.preco)) AS valor_medio_contrato
        FROM adjudicantes adj
        JOIN contratos c ON adj.nif = c.adjudicante
        GROUP BY adj.designacao
        ORDER BY valor_medio_contrato DESC
        LIMIT 5;
    ''').fetchall()

    # Query para a pergunta 6
    pergunta6 = conn.execute('''
        WITH contratos_centralizados AS (SELECT count (c.id) AS quantidade_centralizados
        FROM contratos c 
        WHERE c.procedimento_centralizado = 'Sim'),
        contratos_nao_centralizados AS (SELECT count(c.id) AS quantidade_nao_centralizados
        FROM contratos c
        WHERE c.procedimento_centralizado = 'Não')
        SELECT 
        (SELECT quantidade_centralizados FROM contratos_centralizados) AS centralizados,
        (SELECT quantidade_nao_centralizados FROM contratos_nao_centralizados) AS nao_centralizados
    ''').fetchall()

    # Query para a pergunta 7
    pergunta7 = conn.execute('''
        SELECT ano, mes, dia, max(quantidade) as quantidade
        FROM (
            SELECT dp.ano as ano, dp.mes as mes, dp.dia as dia, count(c.id) AS quantidade
            FROM data_publicacao dp
            JOIN contratos c ON dp.id = c.id
            GROUP BY dp.ano, dp.mes, dp.dia)
    ''').fetchone()

    # Query para a pergunta 8
    pergunta8 = conn.execute('''
        SELECT c.id, c.objeto_contrato, adj.designacao
        FROM contratos c
        JOIN acordo_quadro aq ON c.id = aq.id_contrato
        JOIN adjudicantes adj ON c.adjudicante = adj.nif
        WHERE aq.descr_acordo_quadro IS NOT NULL
        ORDER BY c.id LIMIT 5
    ''').fetchall()

    # Query para a pergunta 9
    pergunta9 = conn.execute('''
        SELECT tc.tipo, count(c.id) AS quantidade
        FROM contratos c
        JOIN tipocontr_contratos tcc ON c.id = tcc.id
        JOIN tipo_contratos tc on tcc.linha_num = tc.linha_num
        GROUP BY tc.tipo
        ORDER BY quantidade desc
    ''').fetchall()

    # Query para a pergunta 10
    pergunta10 = conn.execute('''
        WITH contratos_por_tipo AS (
            SELECT tc.tipo AS tipo_contrato, adj.designacao AS adjudicante, COUNT(c.id) AS quantidade
            FROM contratos c
            JOIN adjudicantes adj ON c.adjudicante = adj.nif
            JOIN tipocontr_contratos tcc ON c.id = tcc.id
            JOIN tipo_contratos tc ON tcc.linha_num = tc.linha_num
            GROUP BY tipo_contrato, adjudicante
        ),
        max_por_tipo AS (
            SELECT tipo_contrato, MAX(quantidade) AS max_contratos
            FROM contratos_por_tipo
            GROUP BY tipo_contrato
        )
        SELECT cpt.tipo_contrato, cpt.adjudicante, cpt.quantidade
        FROM contratos_por_tipo cpt
        JOIN max_por_tipo mpt ON cpt.tipo_contrato = mpt.tipo_contrato AND cpt.quantidade = mpt.max_contratos
        ORDER BY cpt.quantidade DESC, cpt.tipo_contrato
    ''').fetchall()

    conn.close()

    return render_template("questoes.html", pergunta1=pergunta1, pergunta2=pergunta2, pergunta3=pergunta3, pergunta4=pergunta4, pergunta5=pergunta5, pergunta6=pergunta6, pergunta7=pergunta7, pergunta8=pergunta8, pergunta9=pergunta9, pergunta10=pergunta10)

@app.route("/locais", methods=["GET"])
def locais():
    conn = get_db_connection()

    pais_selecionado = request.args.get("pais")
    distrito_selecionado = request.args.get("distrito")
    concelho_selecionado = request.args.get("concelho")

    query = '''
        SELECT c.id, c.objeto_contrato as oc, l.pais, l.distrito, l.concelho
        FROM contratos c
        JOIN locais_contratos lc ON c.id = lc.contratos
        JOIN locais l ON lc.cod_local = l.cod_local
    '''
    conditions = []
    params = []
    if pais_selecionado:
        conditions.append("l.pais = ?")
        params.append(pais_selecionado)
    if distrito_selecionado:
        conditions.append("l.distrito = ?")
        params.append(distrito_selecionado)
    if concelho_selecionado:
        conditions.append("l.concelho LIKE ?")
        params.append('%' + concelho_selecionado + '%')

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    contratos = conn.execute(query, params).fetchall()
    conn.close()

    return render_template("locais.html", contratos=contratos)

@app.route("/api/distritos", methods=["GET"])
def obter_distritos():
    pais = request.args.get("pais")

    if not pais:
        return ({"error": "País não fornecido"}), 400

    conn = get_db_connection()
    distritos = conn.execute('''
        SELECT DISTINCT distrito
        FROM locais l
        WHERE l.pais = ?
        ORDER BY distrito
    ''', (pais,)).fetchall()
    conn.close()

    distritos = [d[0] for d in distritos]
    return ({"distritos": distritos})

@app.route("/api/concelhos", methods=["GET"])
def obter_concelhos():
    distrito = request.args.get("distrito")

    if not distrito:
        return ({"error": "Distrito não fornecido"}), 400

    conn = get_db_connection()
    concelhos = conn.execute('''
        SELECT DISTINCT concelho
        FROM locais l
        WHERE l.distrito = ?
        ORDER BY concelho
    ''', (distrito,)).fetchall()
    conn.close()

    concelhos = [c[0] for c in concelhos]
    return ({"concelhos": concelhos})

@app.route("/Read Me")
def Readme():
    return render_template("Read Me.html")


if __name__ == '__main__':
    app.run(debug=True)
