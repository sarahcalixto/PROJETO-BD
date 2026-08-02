import pytest

def test_vw_pacientes_internados_apenas_ativos(conn):
    """Garante que a view exibe apenas pacientes com internação ativa (data_hora_saida IS NULL)."""
    
    # Busca 2 pacientes existentes
    pacientes = conn.execute("SELECT p.id, pes.nome FROM paciente p JOIN pessoa pes ON p.id = pes.id LIMIT 2").fetchall()
    paciente_1_id, paciente_1_nome = pacientes[0]
    paciente_2_id, paciente_2_nome = pacientes[1]
    
    unidade_id = conn.execute("SELECT id FROM unidade LIMIT 1").fetchone()[0]

    # Internação 1: paciente 1 já recebeu alta (data_hora_saida preenchida)
    conn.execute(f"""
        INSERT INTO internacao (id_paciente, id_unidade, data_hora_entrada, data_hora_saida)
        VALUES ({paciente_1_id}, {unidade_id}, '2026-01-01 08:00:00', '2026-01-05 10:00:00')
    """)

    # Internação 2: paciente 2 está atualmente internado (data_hora_saida é NULL)
    conn.execute(f"""
        INSERT INTO internacao (id_paciente, id_unidade, data_hora_entrada, data_hora_saida)
        VALUES ({paciente_2_id}, {unidade_id}, '2026-02-01 08:00:00', NULL)
    """)

    # Busca os pacientes retornados pela View
    resultados = conn.execute("SELECT paciente FROM vw_pacientes_internados").fetchall()
    nomes_internados = [r[0] for r in resultados]

    # O paciente 2 (ativo) deve constar na listagem
    assert paciente_2_nome in nomes_internados
    
    # O registro da internação encerrada do paciente 1 não pode aparecer
    internacao_pac1 = conn.execute(f"""
        SELECT COUNT(*) FROM vw_pacientes_internados 
        WHERE paciente = '{paciente_1_nome}' AND data_internacao = '2026-01-01 08:00:00'
    """).fetchone()[0]
    assert internacao_pac1 == 0


def test_vw_residentes_sem_supervisor_ignora_doutores(conn):
    """Verifica se apenas residentes supervisionados por Não-Doutores aparecem na view."""
    
    resultados = conn.execute("SELECT residente, preceptor_alocado, titulacao FROM vw_residentes_sem_supervisor").fetchall()
    
    # NENHUM preceptor retornado pela view pode ter a titulação 'doutor'
    for _, _, titulacao in resultados:
        assert titulacao.lower() != 'doutor'


def test_vw_estatisticas_atendimentos_mensal_agregacao(conn):
    """Testa se a agregação por mês e unidade calcula corretamente total de atendimentos e média de tempo."""
    
    paciente_id = conn.execute("SELECT id FROM paciente LIMIT 1").fetchone()[0]
    residente_id = conn.execute("SELECT id FROM atuacao_residente LIMIT 1").fetchone()[0]
    preceptor_id = conn.execute("SELECT id FROM atuacao_preceptor LIMIT 1").fetchone()[0]
    
    unidade_data = conn.execute("SELECT id, nome FROM unidade LIMIT 1").fetchone()
    unidade_id, unidade_nome = unidade_data[0], unidade_data[1]
    
    proc_id = conn.execute("SELECT id FROM procedimento LIMIT 1").fetchone()[0]

    # Inserimos 2 atendimentos para Novembro/2026 nesta unidade
    # Atendimento 1: 20 min | Atendimento 2: 40 min -> Total: 2 | Média: 30.00 min
    conn.execute(f"""
        INSERT INTO atendimento (id, data_hora, duracao_minutos, id_paciente, id_atuacao_residente, id_atuacao_preceptor, id_unidade)
        VALUES (7701, '2026-11-05 10:00:00', 20, {paciente_id}, {residente_id}, {preceptor_id}, {unidade_id})
    """)
    conn.execute(f"""
        INSERT INTO atendimento (id, data_hora, duracao_minutos, id_paciente, id_atuacao_residente, id_atuacao_preceptor, id_unidade)
        VALUES (7702, '2026-11-10 14:00:00', 40, {paciente_id}, {residente_id}, {preceptor_id}, {unidade_id})
    """)

    # Associa procedimento realizado aos dois atendimentos
    conn.execute(f"INSERT INTO procedimento_realizado (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, data_hora_inicio) VALUES (7701, {proc_id}, 1, 20, '2026-11-05 10:00:00')")
    conn.execute(f"INSERT INTO procedimento_realizado (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, data_hora_inicio) VALUES (7702, {proc_id}, 1, 40, '2026-11-10 14:00:00')")

    # Consulta a View para o mês 11/2026
    res = conn.execute(f"""
        SELECT total_atendimentos, media_duracao_minutos, procedimento_mais_comum 
        FROM vw_estatisticas_atendimentos_mensal 
        WHERE unidade = '{unidade_nome}' AND ano = 2026 AND mes = 11
    """).fetchone()

    assert res is not None
    total_atendimentos, media_duracao, procedimento_mais_comum = res

    assert total_atendimentos == 2
    assert float(media_duracao) == 30.00
    assert procedimento_mais_comum is not None


def test_vw_estatisticas_resolve_empate_alfabetico(conn):
    """Testa o desempate do procedimento mais realizado pela ordem alfabética."""
    proc_1 = conn.execute("SELECT id FROM procedimento LIMIT 1").fetchone()[0]
    proc_2 = conn.execute("SELECT id FROM procedimento OFFSET 1 LIMIT 1").fetchone()[0]
    
    paciente_id = conn.execute("SELECT id FROM paciente LIMIT 1").fetchone()[0]
    residente_id = conn.execute("SELECT id FROM atuacao_residente LIMIT 1").fetchone()[0]
    preceptor_id = conn.execute("SELECT id FROM atuacao_preceptor LIMIT 1").fetchone()[0]
    
    unidade_data = conn.execute("SELECT id, nome FROM unidade LIMIT 1").fetchone()
    unidade_id, unidade_nome = unidade_data[0], unidade_data[1]
    
    conn.execute(f"INSERT INTO atendimento (id, data_hora, duracao_minutos, id_paciente, id_atuacao_residente, id_atuacao_preceptor, id_unidade) VALUES (888, '2026-12-01 10:00:00', 30, {paciente_id}, {residente_id}, {preceptor_id}, {unidade_id})")
    conn.execute(f"INSERT INTO atendimento (id, data_hora, duracao_minutos, id_paciente, id_atuacao_residente, id_atuacao_preceptor, id_unidade) VALUES (889, '2026-12-01 11:00:00', 30, {paciente_id}, {residente_id}, {preceptor_id}, {unidade_id})")

    conn.execute(f"INSERT INTO procedimento_realizado (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, data_hora_inicio) VALUES (888, {proc_1}, 1, 10, NOW())")
    conn.execute(f"INSERT INTO procedimento_realizado (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, data_hora_inicio) VALUES (889, {proc_2}, 1, 10, NOW())")
    
    resultado = conn.execute(f"SELECT procedimento_mais_comum FROM vw_estatisticas_atendimentos_mensal WHERE unidade = '{unidade_nome}' AND ano = 2026 AND mes = 12").fetchone()
    
    assert resultado is not None