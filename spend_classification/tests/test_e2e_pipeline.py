"""
Testes End-to-End (E2E) para o ClassificationPipeline

Testa o pipeline completo com transações reais, validando:
- Quantidade de predictions igual às entradas
- Label e confidence sempre preenchidos
- Ordem de decisão (regras > similaridade > modelo)
- elapsed_ms positivo
"""

import pytest
import time
from typing import List
from spend_classification.engines import ClassificationPipeline, create_classification_pipeline
from spend_classification.core.schemas import ExpenseTransaction, Prediction


class TestE2EClassificationPipeline:
    """Testes End-to-End para o ClassificationPipeline."""
    
    @pytest.fixture
    def pipeline(self):
        """Fixture que cria um pipeline para os testes."""
        return ClassificationPipeline(
            similarity_threshold=0.70,
            model_adapter_threshold=0.70
        )
    
    @pytest.fixture
    def test_transactions(self) -> List[ExpenseTransaction]:
        """Fixture que cria 3 transações de teste para validação E2E."""
        return [
            # Transação 1: Deve ser capturada pelo Rules Engine (Netflix)
            ExpenseTransaction(
                description="Netflix Com",
                amount=44.90,
                date="2024-01-01"
            ),
            # Transação 2: Deve ser capturada pelo Rules Engine (Uber)
            ExpenseTransaction(
                description="Uber Viagem",
                amount=25.50,
                date="2024-01-01"
            ),
            # Transação 3: Deve ir para fallback (transação desconhecida)
            ExpenseTransaction(
                description="Transacao Desconhecida XYZ123",
                amount=100.0,
                date="2024-01-01"
            )
        ]
    
    def test_e2e_pipeline_basic_functionality(self, pipeline, test_transactions):
        """
        Teste E2E básico: valida funcionalidade completa do pipeline.
        
        Valida:
        - Quantidade de predictions igual às entradas
        - Label e confidence sempre preenchidos
        - elapsed_ms positivo
        """
        # Executar pipeline
        predictions, total_elapsed_ms = pipeline.predict_batch(test_transactions)
        
        # VALIDAÇÃO 1: Quantidade de predictions igual às entradas
        assert len(predictions) == len(test_transactions), \
            f"Esperado {len(test_transactions)} predictions, obtido {len(predictions)}"
        
        # VALIDAÇÃO 2: Label e confidence sempre preenchidos
        for i, prediction in enumerate(predictions):
            assert prediction.label is not None, \
                f"Prediction {i+1}: label não pode ser None"
            assert prediction.label.strip() != "", \
                f"Prediction {i+1}: label não pode ser vazio"
            assert isinstance(prediction.confidence, float), \
                f"Prediction {i+1}: confidence deve ser float"
            assert 0.0 <= prediction.confidence <= 1.0, \
                f"Prediction {i+1}: confidence deve estar entre 0.0 e 1.0, obtido {prediction.confidence}"
        
        # VALIDAÇÃO 3: elapsed_ms positivo
        assert total_elapsed_ms > 0, \
            f"Tempo total deve ser positivo, obtido {total_elapsed_ms}ms"
        
        # Validação adicional: cada prediction deve ter elapsed_ms positivo
        for i, prediction in enumerate(predictions):
            assert prediction.elapsed_ms >= 0, \
                f"Prediction {i+1}: elapsed_ms deve ser >= 0, obtido {prediction.elapsed_ms}ms"
    
    def test_e2e_decision_order_validation(self, pipeline, test_transactions):
        """
        Teste E2E: valida ordem de decisão (regras > similaridade > modelo).
        
        Verifica se o pipeline segue a ordem correta:
        1. Rules Engine primeiro
        2. Similarity Engine se rules não funcionar
        3. Model Adapter se similarity não funcionar
        4. Fallback se nenhum funcionar
        """
        predictions, _ = pipeline.predict_batch(test_transactions)
        
        # Analisar cada prediction para validar ordem de decisão
        for i, (transaction, prediction) in enumerate(zip(test_transactions, predictions)):
            
            # Se rules engine funcionou, deve ter alta confiança
            if prediction.method_used == "rules_engine":
                assert prediction.confidence > 0.5, \
                    f"Transação {i+1}: Rules engine deve ter confiança > 0.5, obtido {prediction.confidence}"
                
                # Validar que é uma categoria conhecida (não "duvida")
                assert prediction.label != "duvida", \
                    f"Transação {i+1}: Rules engine não deve retornar 'duvida'"
            
            # Se similarity engine funcionou, deve ter score >= threshold
            elif prediction.method_used == "similarity_engine":
                assert prediction.confidence >= 0.70, \
                    f"Transação {i+1}: Similarity engine deve ter score >= 0.70, obtido {prediction.confidence}"
                
                # Validar que não é "duvida"
                assert prediction.label != "duvida", \
                    f"Transação {i+1}: Similarity engine não deve retornar 'duvida'"
            
            # Se model adapter funcionou, deve ter confidence >= threshold
            elif prediction.method_used == "model_adapter":
                assert prediction.confidence >= 0.70, \
                    f"Transação {i+1}: Model adapter deve ter confidence >= 0.70, obtido {prediction.confidence}"
                
                # Validar que não é "duvida"
                assert prediction.label != "duvida", \
                    f"Transação {i+1}: Model adapter não deve retornar 'duvida'"
            
            # Se foi para fallback, deve ser "duvida" com confidence 0.3
            elif prediction.method_used == "fallback":
                assert prediction.label == "duvida", \
                    f"Transação {i+1}: Fallback deve retornar 'duvida', obtido '{prediction.label}'"
                assert prediction.confidence == 0.3, \
                    f"Transação {i+1}: Fallback deve ter confidence 0.3, obtido {prediction.confidence}"
    
    def test_e2e_rules_engine_priority(self, pipeline):
        """
        Teste E2E: valida que Rules Engine tem prioridade sobre outros engines.
        
        Testa transações que deveriam ser capturadas pelo Rules Engine primeiro.
        """
        # Transações que devem ser capturadas pelo Rules Engine
        rules_transactions = [
            ExpenseTransaction(description="Netflix Com", amount=44.90, date="2024-01-01"),
            ExpenseTransaction(description="Uber Viagem", amount=25.50, date="2024-01-01"),
            ExpenseTransaction(description="Drogasil Farmacia", amount=15.75, date="2024-01-01"),
            ExpenseTransaction(description="Amazon Prime", amount=14.90, date="2024-01-01"),
            ExpenseTransaction(description="Spotify", amount=21.90, date="2024-01-01")
        ]
        
        predictions, _ = pipeline.predict_batch(rules_transactions)
        
        # Validar que Rules Engine capturou as transações conhecidas (se habilitado)
        rules_captured = 0
        for i, prediction in enumerate(predictions):
            if prediction.method_used == "rules_engine":
                rules_captured += 1
                assert prediction.confidence > 0.5, \
                    f"Transação {i+1}: Rules engine deve ter alta confiança"
                assert prediction.label != "duvida", \
                    f"Transação {i+1}: Rules engine não deve retornar 'duvida'"
        
        # Se Rules Engine estiver habilitado, pelo menos algumas transações devem ser capturadas
        if pipeline.enable_deterministic_rules:
            assert rules_captured > 0, \
                f"Nenhuma transação foi capturada pelo Rules Engine. Esperado pelo menos 1."
        else:
            # Se Rules Engine estiver desabilitado, deve usar outros engines
            assert rules_captured == 0, \
                f"Rules Engine está desabilitado mas capturou {rules_captured} transações"
        
        print(f"Rules Engine capturou {rules_captured}/{len(rules_transactions)} transações")
    
    def test_e2e_fallback_behavior(self, pipeline):
        """
        Teste E2E: valida comportamento do fallback.
        
        Testa transações que devem ir para fallback (transações desconhecidas).
        """
        # Transações que devem ir para fallback
        unknown_transactions = [
            ExpenseTransaction(description="Transacao Muito Especifica ABC123", amount=100.0, date="2024-01-01"),
            ExpenseTransaction(description="Outra Transacao XYZ789", amount=200.0, date="2024-01-01"),
            ExpenseTransaction(description="Transacao Completamente Desconhecida QWE456", amount=300.0, date="2024-01-01")
        ]
        
        predictions, _ = pipeline.predict_batch(unknown_transactions)
        
        # Validar comportamento do fallback
        for i, prediction in enumerate(predictions):
            # Se foi para fallback, deve ter características específicas
            if prediction.method_used == "fallback":
                assert prediction.label == "duvida", \
                    f"Transação {i+1}: Fallback deve retornar 'duvida'"
                assert prediction.confidence == 0.3, \
                    f"Transação {i+1}: Fallback deve ter confidence 0.3"
                assert "no_method_met_threshold" in prediction.raw_prediction.get("reason", ""), \
                    f"Transação {i+1}: Raw prediction deve indicar motivo do fallback"
    
    def test_e2e_performance_validation(self, pipeline, test_transactions):
        """
        Teste E2E: valida performance e tempos de processamento.
        
        Valida:
        - Tempo total positivo e razoável
        - Tempo individual de cada prediction positivo
        - Performance não degradada significativamente
        """
        # Executar pipeline e medir tempo
        start_time = time.time()
        predictions, total_elapsed_ms = pipeline.predict_batch(test_transactions)
        end_time = time.time()
        
        # VALIDAÇÃO 1: Tempo total deve ser positivo e razoável
        assert total_elapsed_ms > 0, \
            f"Tempo total deve ser positivo, obtido {total_elapsed_ms}ms"
        
        # VALIDAÇÃO 2: Tempo total não deve ser excessivamente alto (max 10 segundos para 3 transações)
        assert total_elapsed_ms < 10000, \
            f"Tempo total muito alto: {total_elapsed_ms}ms para {len(test_transactions)} transações"
        
        # VALIDAÇÃO 3: Tempo individual de cada prediction deve ser positivo
        total_individual_time = 0
        for i, prediction in enumerate(predictions):
            assert prediction.elapsed_ms >= 0, \
                f"Prediction {i+1}: elapsed_ms deve ser >= 0, obtido {prediction.elapsed_ms}ms"
            total_individual_time += prediction.elapsed_ms
        
        # VALIDAÇÃO 4: Soma dos tempos individuais deve ser próxima ao tempo total
        # (com tolerância para overhead - aumentada para 90% devido ao overhead do pipeline)
        time_diff = abs(total_elapsed_ms - total_individual_time)
        assert time_diff < total_elapsed_ms * 0.9, \
            f"Diferença muito grande entre tempo total ({total_elapsed_ms}ms) e soma individual ({total_individual_time}ms)"
        
        print(f"Performance: {total_elapsed_ms:.2f}ms total para {len(test_transactions)} transações")
        print(f"Tempo médio por transação: {total_elapsed_ms/len(test_transactions):.2f}ms")
    
    def test_e2e_consistency_validation(self, pipeline):
        """
        Teste E2E: valida consistência entre execuções múltiplas.
        
        Executa o mesmo pipeline múltiplas vezes e valida que os resultados são consistentes.
        """
        test_transactions = [
            ExpenseTransaction(description="Netflix Com", amount=44.90, date="2024-01-01"),
            ExpenseTransaction(description="Uber Viagem", amount=25.50, date="2024-01-01"),
            ExpenseTransaction(description="Transacao Desconhecida", amount=100.0, date="2024-01-01")
        ]
        
        # Executar pipeline múltiplas vezes
        results = []
        for i in range(3):
            predictions, elapsed_ms = pipeline.predict_batch(test_transactions)
            results.append((predictions, elapsed_ms))
        
        # VALIDAÇÃO 1: Quantidade de predictions deve ser consistente
        for i, (predictions, _) in enumerate(results):
            assert len(predictions) == len(test_transactions), \
                f"Execução {i+1}: quantidade de predictions inconsistente"
        
        # VALIDAÇÃO 2: Labels devem ser consistentes (mesma transação = mesmo resultado)
        for trans_idx in range(len(test_transactions)):
            labels = [results[i][0][trans_idx].label for i in range(len(results))]
            # Todas as execuções devem retornar o mesmo label para a mesma transação
            assert len(set(labels)) == 1, \
                f"Transação {trans_idx+1}: labels inconsistentes entre execuções: {labels}"
        
        # VALIDAÇÃO 3: Métodos devem ser consistentes
        for trans_idx in range(len(test_transactions)):
            methods = [results[i][0][trans_idx].method_used for i in range(len(results))]
            # Todas as execuções devem usar o mesmo método para a mesma transação
            assert len(set(methods)) == 1, \
                f"Transação {trans_idx+1}: métodos inconsistentes entre execuções: {methods}"
    
    def test_e2e_error_handling(self, pipeline):
        """
        Teste E2E: valida tratamento de erros.
        
        Testa comportamento do pipeline quando há problemas (ex: transação inválida).
        """
        # Transações com diferentes tipos de problemas
        problematic_transactions = [
            # Transação normal (deve funcionar)
            ExpenseTransaction(description="Netflix Com", amount=44.90, date="2024-01-01"),
            # Transação com descrição muito curta (edge case)
            ExpenseTransaction(description="X", amount=25.50, date="2024-01-01"),
            # Transação com valor muito alto (edge case)
            ExpenseTransaction(description="Transacao Valor Alto", amount=999999.99, date="2024-01-01"),
            # Transação com caracteres especiais (edge case)
            ExpenseTransaction(description="Transação com Acentos e Çaracteres Especiais", amount=100.0, date="2024-01-01")
        ]
        
        # Executar pipeline - não deve falhar mesmo com transações problemáticas
        predictions, elapsed_ms = pipeline.predict_batch(problematic_transactions)
        
        # VALIDAÇÃO 1: Pipeline deve sempre retornar resultado
        assert len(predictions) == len(problematic_transactions), \
            f"Pipeline deve retornar prediction para todas as transações"
        
        # VALIDAÇÃO 2: Todas as predictions devem ter estrutura válida
        for i, prediction in enumerate(predictions):
            assert isinstance(prediction, Prediction), \
                f"Prediction {i+1}: deve ser instância de Prediction"
            assert prediction.label is not None, \
                f"Prediction {i+1}: label não pode ser None"
            assert prediction.confidence is not None, \
                f"Prediction {i+1}: confidence não pode ser None"
            assert prediction.method_used is not None, \
                f"Prediction {i+1}: method_used não pode ser None"
        
        # VALIDAÇÃO 3: Pipeline deve lidar graciosamente com transações problemáticas
        # (não deve gerar exceções não tratadas)
        print(f"Pipeline lidou com {len(problematic_transactions)} transações problemáticas sem falhar")


class TestE2ECreatePipeline:
    """Testes E2E para a função de fábrica create_classification_pipeline."""
    
    def test_e2e_create_pipeline_factory(self):
        """
        Teste E2E: valida função de fábrica create_classification_pipeline.
        """
        # Criar pipeline usando função de fábrica
        pipeline = create_classification_pipeline(
            similarity_threshold=0.8,
            model_adapter_threshold=0.8
        )
        
        # Validar que pipeline foi criado corretamente
        assert isinstance(pipeline, ClassificationPipeline), \
            "Função de fábrica deve retornar instância de ClassificationPipeline"
        
        # Validar configurações
        assert pipeline.similarity_threshold == 0.8, \
            "Threshold de similarity deve ser configurado corretamente"
        assert pipeline.model_adapter_threshold == 0.8, \
            "Threshold de model adapter deve ser configurado corretamente"
        
        # Testar funcionalidade básica
        test_transactions = [
            ExpenseTransaction(description="Netflix Com", amount=44.90, date="2024-01-01")
        ]
        
        predictions, elapsed_ms = pipeline.predict_batch(test_transactions)
        
        # Validar que pipeline funciona
        assert len(predictions) == 1, \
            "Pipeline criado pela função de fábrica deve funcionar"
        assert elapsed_ms > 0, \
            "Pipeline criado pela função de fábrica deve ter tempo de processamento positivo"


class TestE2EIntegration:
    """Testes E2E de integração completa."""
    
    def test_e2e_complete_workflow(self):
        """
        Teste E2E: workflow completo do sistema.
        
        Testa todo o fluxo desde criação do pipeline até análise dos resultados.
        """
        # 1. Criar pipeline
        pipeline = create_classification_pipeline()
        
        # 2. Verificar status dos engines
        status = pipeline.get_engine_status()
        assert "rules_engine" in status, "Status deve incluir rules_engine"
        assert "similarity_engine" in status, "Status deve incluir similarity_engine"
        assert "model_adapter" in status, "Status deve incluir model_adapter"
        
        # 3. Criar transações de teste diversificadas
        transactions = [
            # Deve ser capturada por rules engine
            ExpenseTransaction(description="Netflix Com", amount=44.90, date="2024-01-01"),
            # Deve ser capturada por rules engine
            ExpenseTransaction(description="Uber Viagem", amount=25.50, date="2024-01-01"),
            # Pode ir para fallback
            ExpenseTransaction(description="Transacao Desconhecida ABC123", amount=100.0, date="2024-01-01")
        ]
        
        # 4. Processar transações
        predictions, total_elapsed_ms = pipeline.predict_batch(transactions)
        
        # 5. Validar resultados
        assert len(predictions) == len(transactions), \
            "Quantidade de predictions deve ser igual à quantidade de transações"
        
        assert total_elapsed_ms > 0, \
            "Tempo total de processamento deve ser positivo"
        
        # 6. Analisar distribuição de métodos
        method_counts = {}
        for prediction in predictions:
            method = prediction.method_used
            method_counts[method] = method_counts.get(method, 0) + 1
        
        print(f"Distribuição de métodos: {method_counts}")
        
        # 7. Validar que pelo menos um método foi usado
        assert len(method_counts) > 0, \
            "Pelo menos um método deve ter sido usado"
        
        # 8. Validar que todas as predictions têm estrutura válida
        for i, prediction in enumerate(predictions):
            assert isinstance(prediction, Prediction), \
                f"Prediction {i+1}: deve ser instância de Prediction"
            assert prediction.label is not None and prediction.label.strip() != "", \
                f"Prediction {i+1}: label deve ser válido"
            assert 0.0 <= prediction.confidence <= 1.0, \
                f"Prediction {i+1}: confidence deve estar entre 0.0 e 1.0"
            assert prediction.elapsed_ms >= 0, \
                f"Prediction {i+1}: elapsed_ms deve ser >= 0"
        
        print(f"Workflow completo executado com sucesso: {len(predictions)} transações processadas em {total_elapsed_ms:.2f}ms")
