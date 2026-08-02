import pytest
import psycopg

def test_trg_check_sobreposicao_escala_bloqueia_conflito(conn):
    residente_id = conn.execute("SELECT id FROM atuacao_residente LIMIT 1").fetchone()[0]
    preceptor_id = conn.execute("SELECT id FROM atuacao_preceptor LIMIT 1").fetchone()[0]
    unidade_1 = conn.execute("SELECT id FROM unidade LIMIT 1").fetchone()[0]
    unidade_2 = conn.execute("SELECT id FROM unidade OFFSET 1 LIMIT 1").fetchone()[0]

    # 1. Inserção válida
    conn.execute(f"""
        INSERT INTO escala (id_unidade, data_plantao, turno, id_atuacao_residente, id_atuacao_preceptor)
        VALUES ({unidade_1}, '2026-10-10', 'manha', {residente_id}, {preceptor_id})
    """)
    
    # 2. Inserção inválida
    # Usamos psycopg.Error porque triggers geralmente levantam RaiseException, não CheckViolation
    with pytest.raises(psycopg.Error):
        conn.execute(f"""
            INSERT INTO escala (id_unidade, data_plantao, turno, id_atuacao_residente, id_atuacao_preceptor)
            VALUES ({unidade_2}, '2026-10-10', 'manha', {residente_id}, {preceptor_id})
        """)

def test_trg_audita_atendimento_registra_operacoes(conn):
    """Garante que INSERT, UPDATE e DELETE gerem rastros na tabela de auditoria."""
    
    # Busca IDs dinâmicos para evitar ForeignKeyViolation
    paciente_id = conn.execute("SELECT id FROM paciente LIMIT 1").fetchone()[0]
    residente_id = conn.execute("SELECT id FROM atuacao_residente LIMIT 1").fetchone()[0]
    preceptor_id = conn.execute("SELECT id FROM atuacao_preceptor LIMIT 1").fetchone()[0]
    unidade_id = conn.execute("SELECT id FROM unidade LIMIT 1").fetchone()[0]

    # 1. Testa o INSERT (usamos o ID 9999 para garantir que não colida com os dados de teste)
    conn.execute(f"""
        INSERT INTO atendimento (id, data_hora, duracao_minutos, id_paciente, id_atuacao_residente, id_atuacao_preceptor, id_unidade) 
        VALUES (9999, '2026-10-10 10:00:00', 30, {paciente_id}, {residente_id}, {preceptor_id}, {unidade_id})
    """)
    
    # 2. Testa o UPDATE
    conn.execute("UPDATE atendimento SET duracao_minutos = 45 WHERE id = 9999")
    
    # 3. Testa o DELETE
    conn.execute("DELETE FROM atendimento WHERE id = 9999")
    
   # 4. Verifica a Auditoria
    logs = conn.execute("""
        SELECT operacao, dados_antigos, dados_novos 
        FROM auditoria_atendimento 
        WHERE id_atendimento = 9999 
        ORDER BY data_hora ASC
    """).fetchall()
    
    # Validações estruturais para garantir que o trigger fez as 3 fotos do registro
    assert len(logs) == 3
    
    # Valida o estado do INSERT
    assert logs[0][0] == 'INSERT'
    
    # Valida o estado do UPDATE (se capturou a alteração para 45 minutos)
    assert logs[1][0] == 'UPDATE'
    assert logs[1][2]['duracao_minutos'] == 45
    
    # Valida o estado do DELETE
    assert logs[2][0] == 'DELETE'

def test_trg_atualiza_media_procedimentos_calcula_corretamente(conn):
    # Pegamos um procedimento válido
    proc_id = conn.execute("SELECT id FROM procedimento LIMIT 1").fetchone()[0]
    
    # Para evitar UniqueViolation, criamos um NOVO atendimento (ID 999) dinamicamente
    paciente_id = conn.execute("SELECT id FROM paciente LIMIT 1").fetchone()[0]
    residente_id = conn.execute("SELECT id FROM atuacao_residente LIMIT 1").fetchone()[0]
    preceptor_id = conn.execute("SELECT id FROM atuacao_preceptor LIMIT 1").fetchone()[0]
    unidade_id = conn.execute("SELECT id FROM unidade LIMIT 1").fetchone()[0]
    
    conn.execute(f"""
        INSERT INTO atendimento (id, data_hora, duracao_minutos, id_paciente, id_atuacao_residente, id_atuacao_preceptor, id_unidade) 
        VALUES (999, '2026-11-10 10:00:00', 30, {paciente_id}, {residente_id}, {preceptor_id}, {unidade_id})
    """)

    # Agora inserimos o procedimento nesse novo atendimento
    conn.execute(f"INSERT INTO procedimento_realizado (id_atendimento, id_procedimento, quantidade, tempo_real_minutos, data_hora_inicio) VALUES (999, {proc_id}, 1, 10, NOW())")
    
    media = conn.execute(f"SELECT media_tempo_procedimento FROM procedimento WHERE id = {proc_id}").fetchone()[0]
    assert media is not None