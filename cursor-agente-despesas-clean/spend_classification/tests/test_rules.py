"""
Testes para o módulo rules.py

Testa todas as funções puras de inferência de regras.
"""

import pytest
from ..engines.rules import (
    infer_tipo_from_card,
    infer_comp_from_card,
    parse_parcelas_from_desc,
    infer_titular_from_card,
    infer_final_cartao_from_card,
    apply_comp_rules_by_titular,
    clean_transaction_description,
    extract_establishment_name,
    validate_parcelas_consistency,
    get_rule_confidence
)


class TestInferTipoFromCard:
    """Testa a função infer_tipo_from_card."""
    
    def test_cc_prefix_returns_debito(self):
        """Testa que cartão com CC - retorna débito."""
        result = infer_tipo_from_card("CC - 1234")
        
        assert result is not None
        assert result.category == "débito"
        assert result.confidence == 0.95
        assert result.classifier_used == "rules_tipo"
        assert not result.fallback_used
        assert result.raw_prediction["rule_applied"] == "cc_prefix"
    
    def test_cc_prefix_case_insensitive(self):
        """Testa que CC - funciona em qualquer case."""
        result = infer_tipo_from_card("cc - 1234")
        
        assert result is not None
        assert result.category == "débito"
    
    def test_cc_prefix_with_spaces(self):
        """Testa que CC - funciona com espaços extras."""
        result = infer_tipo_from_card("  CC -  1234  ")
        
        assert result is not None
        assert result.category == "débito"
    
    def test_no_cc_prefix_returns_none(self):
        """Testa que cartão sem CC - retorna None."""
        result = infer_tipo_from_card("VISA 1234")
        
        assert result is None
    
    def test_empty_card_returns_none(self):
        """Testa que cartão vazio retorna None."""
        result = infer_tipo_from_card("")
        
        assert result is None
    
    def test_none_card_returns_none(self):
        """Testa que cartão None retorna None."""
        result = infer_tipo_from_card(None)
        
        assert result is None
    
    def test_non_string_card_returns_none(self):
        """Testa que cartão não-string retorna None."""
        result = infer_tipo_from_card(1234)
        
        assert result is None


class TestInferCompFromCard:
    """Testa a função infer_comp_from_card."""
    
    def test_casa_keyword_returns_planilha_comp(self):
        """Testa que cartão com CASA retorna planilha comp."""
        result = infer_comp_from_card("CASA 1234")
        
        assert result is not None
        assert result.category == "planilha comp"
        assert result.confidence == 0.90
        assert result.classifier_used == "rules_comp"
        assert result.raw_prediction["rule_applied"] == "casa_keyword"
    
    def test_casa_keyword_case_insensitive(self):
        """Testa que CASA funciona em qualquer case."""
        result = infer_comp_from_card("casa 1234")
        
        assert result is not None
        assert result.category == "planilha comp"
    
    def test_casa_keyword_within_text(self):
        """Testa que CASA funciona dentro do texto."""
        result = infer_comp_from_card("CARTÃO CASA 1234")
        
        assert result is not None
        assert result.category == "planilha comp"
    
    def test_no_casa_keyword_returns_none(self):
        """Testa que cartão sem CASA retorna None."""
        result = infer_comp_from_card("VISA 1234")
        
        assert result is None
    
    def test_empty_card_returns_none(self):
        """Testa que cartão vazio retorna None."""
        result = infer_comp_from_card("")
        
        assert result is None


class TestParseParcelasFromDesc:
    """Testa a função parse_parcelas_from_desc."""
    
    def test_parentheses_pattern(self):
        """Testa padrão com parênteses (3/12)."""
        result = parse_parcelas_from_desc("Compra (3/12) na loja")
        
        assert result is not None
        assert result["no_da_parcela"] == 3
        assert result["parcelas"] == 12
        assert result["confidence"] == 0.95
    
    def test_brackets_pattern(self):
        """Testa padrão com colchetes [3/12]."""
        result = parse_parcelas_from_desc("Compra [3/12] na loja")
        
        assert result is not None
        assert result["no_da_parcela"] == 3
        assert result["parcelas"] == 12
    
    def test_simple_pattern(self):
        """Testa padrão simples 3/12."""
        result = parse_parcelas_from_desc("Compra 3/12 na loja")
        
        assert result is not None
        assert result["no_da_parcela"] == 3
        assert result["parcelas"] == 12
    
    def test_spaces_in_pattern(self):
        """Testa padrão com espaços ( 3 / 12 )."""
        result = parse_parcelas_from_desc("Compra ( 3 / 12 ) na loja")
        
        assert result is not None
        assert result["no_da_parcela"] == 3
        assert result["parcelas"] == 12
    
    def test_single_digit_numbers(self):
        """Testa números de um dígito."""
        result = parse_parcelas_from_desc("Compra (2/5) na loja")
        
        assert result is not None
        assert result["no_da_parcela"] == 2
        assert result["parcelas"] == 5
    
    def test_double_digit_numbers(self):
        """Testa números de dois dígitos."""
        result = parse_parcelas_from_desc("Compra (10/24) na loja")
        
        assert result is not None
        assert result["no_da_parcela"] == 10
        assert result["parcelas"] == 24
    
    def test_invalid_parcelas_returns_none(self):
        """Testa que parcelas inválidas retornam None."""
        # Parcela atual maior que total
        result = parse_parcelas_from_desc("Compra (5/3) na loja")
        assert result is None
        
        # Números muito grandes
        result = parse_parcelas_from_desc("Compra (100/200) na loja")
        assert result is None
    
    def test_no_pattern_returns_none(self):
        """Testa que descrição sem padrão retorna None."""
        result = parse_parcelas_from_desc("Compra à vista na loja")
        
        assert result is None
    
    def test_empty_description_returns_none(self):
        """Testa que descrição vazia retorna None."""
        result = parse_parcelas_from_desc("")
        
        assert result is None
    
    def test_multiple_patterns_returns_first(self):
        """Testa que múltiplos padrões retorna o primeiro encontrado."""
        result = parse_parcelas_from_desc("Compra (2/6) e (3/12) na loja")
        
        assert result is not None
        assert result["no_da_parcela"] == 2
        assert result["parcelas"] == 6


class TestInferTitularFromCard:
    """Testa a função infer_titular_from_card."""
    
    def test_aline_pattern(self):
        """Testa detecção de titular Aline."""
        result = infer_titular_from_card("CARTÃO ALINE 1234")
        
        assert result == "aline"
    
    def test_angela_pattern(self):
        """Testa detecção de titular Angela."""
        result = infer_titular_from_card("CARTÃO ANGELA 1234")
        
        assert result == "angela"
    
    def test_joao_pattern(self):
        """Testa detecção de titular João."""
        result = infer_titular_from_card("CARTÃO JOÃO 1234")
        
        assert result == "joao"
    
    def test_joao_without_accent(self):
        """Testa detecção de João sem acento."""
        result = infer_titular_from_card("CARTÃO JOAO 1234")
        
        assert result == "joao"
    
    def test_case_insensitive(self):
        """Testa que detecção é case-insensitive."""
        result = infer_titular_from_card("cartão aline 1234")
        
        assert result == "aline"
    
    def test_no_titular_returns_none(self):
        """Testa que cartão sem titular conhecido retorna None."""
        result = infer_titular_from_card("CARTÃO 1234")
        
        assert result is None
    
    def test_empty_card_returns_none(self):
        """Testa que cartão vazio retorna None."""
        result = infer_titular_from_card("")
        
        assert result is None


class TestInferFinalCartaoFromCard:
    """Testa a função infer_final_cartao_from_card."""
    
    def test_extract_four_digits(self):
        """Testa extração de 4 dígitos."""
        result = infer_final_cartao_from_card("CARTÃO 1234567890")
        
        assert result == "5678"  # Última sequência de 4 dígitos encontrada
    
    def test_extract_last_four_digits(self):
        """Testa extração dos últimos 4 dígitos."""
        result = infer_final_cartao_from_card("CARTÃO 1234 5678")
        
        assert result == "5678"  # Últimos 4 dígitos encontrados
    
    def test_no_digits_returns_none(self):
        """Testa que cartão sem dígitos retorna None."""
        result = infer_final_cartao_from_card("CARTÃO SEM NÚMEROS")
        
        assert result is None
    
    def test_empty_card_returns_none(self):
        """Testa que cartão vazio retorna None."""
        result = infer_final_cartao_from_card("")
        
        assert result is None


class TestApplyCompRulesByTitular:
    """Testa a função apply_comp_rules_by_titular."""
    
    def test_angela_always_planilha_comp(self):
        """Testa que Angela sempre retorna planilha comp."""
        result = apply_comp_rules_by_titular("outro", "CARTÃO ANGELA 1234")
        
        assert result == "planilha comp"
    
    def test_aline_planilha_finals(self):
        """Testa regras específicas para finais de cartão da Aline."""
        # Final para planilha comp
        result = apply_comp_rules_by_titular("outro", "CARTÃO ALINE 0951")
        assert result == "planilha comp"
        
        result = apply_comp_rules_by_titular("outro", "CARTÃO ALINE 4147")
        assert result == "planilha comp"
    
    def test_aline_gastos_finals(self):
        """Testa finais específicos para gastos da Aline."""
        result = apply_comp_rules_by_titular("outro", "CARTÃO ALINE 8805")
        assert result == "Gastos Aline"
        
        result = apply_comp_rules_by_titular("outro", "CARTÃO ALINE 9558")
        assert result == "Gastos Aline"
    
    def test_aline_unknown_final_returns_original(self):
        """Testa que Aline com final desconhecido retorna predição original."""
        result = apply_comp_rules_by_titular("predição original", "CARTÃO ALINE 9999")
        
        assert result == "predição original"
    
    def test_joao_doubt_returns_empty(self):
        """Testa que João com dúvida retorna string vazia."""
        result = apply_comp_rules_by_titular("duvida - 0.5", "CARTÃO JOÃO 1234")
        
        assert result == ""
    
    def test_joao_confident_returns_original(self):
        """Testa que João com confiança retorna predição original."""
        result = apply_comp_rules_by_titular("planilha comp", "CARTÃO JOÃO 1234")
        
        assert result == "planilha comp"
    
    def test_unknown_titular_returns_original(self):
        """Testa que titular desconhecido retorna predição original."""
        result = apply_comp_rules_by_titular("predição original", "CARTÃO DESCONHECIDO 1234")
        
        assert result == "predição original"
    
    def test_empty_card_returns_original(self):
        """Testa que cartão vazio retorna predição original."""
        result = apply_comp_rules_by_titular("predição original", "")
        
        assert result == "predição original"


class TestCleanTransactionDescription:
    """Testa a função clean_transaction_description."""
    
    def test_remove_dates(self):
        """Testa remoção de datas."""
        result = clean_transaction_description("Compra 15/03/2024 na loja")
        
        assert result == "Compra na loja"
    
    def test_remove_generic_words(self):
        """Testa remoção de palavras genéricas."""
        result = clean_transaction_description("PAGAMENTO compra na loja")
        
        assert result == "compra na loja"  # "compra" não é removida
    
    def test_remove_multiple_spaces(self):
        """Testa remoção de espaços múltiplos."""
        result = clean_transaction_description("Compra    na    loja")
        
        assert result == "Compra na loja"
    
    def test_empty_description(self):
        """Testa descrição vazia."""
        result = clean_transaction_description("")
        
        assert result == ""
    
    def test_none_description(self):
        """Testa descrição None."""
        result = clean_transaction_description(None)
        
        assert result == ""


class TestExtractEstablishmentName:
    """Testa a função extract_establishment_name."""
    
    def test_remove_prefixes(self):
        """Testa remoção de prefixos."""
        result = extract_establishment_name("PIX LOJA ABC 123")
        
        assert result == "Loja Abc 123"
    
    def test_remove_dates(self):
        """Testa remoção de datas."""
        result = extract_establishment_name("LOJA ABC 15/03/2024")
        
        assert result == "Loja Abc"
    
    def test_remove_symbols(self):
        """Testa remoção de símbolos."""
        result = extract_establishment_name("LOJA ABC - 123")
        
        assert result == "Loja Abc 123"
    
    def test_title_case(self):
        """Testa conversão para título."""
        result = extract_establishment_name("loja abc")
        
        assert result == "Loja Abc"
    
    def test_empty_description(self):
        """Testa descrição vazia."""
        result = extract_establishment_name("")
        
        assert result == ""


class TestValidateParcelasConsistency:
    """Testa a função validate_parcelas_consistency."""
    
    def test_valid_parcelas(self):
        """Testa parcelas válidas."""
        assert validate_parcelas_consistency(3, 12) is True
        assert validate_parcelas_consistency(1, 1) is True
        assert validate_parcelas_consistency(99, 99) is True
    
    def test_invalid_parcelas(self):
        """Testa parcelas inválidas."""
        # Parcela atual maior que total
        assert validate_parcelas_consistency(5, 3) is False
        # Parcela atual zero
        assert validate_parcelas_consistency(0, 12) is False
        # Total zero
        assert validate_parcelas_consistency(3, 0) is False
        # Números muito grandes
        assert validate_parcelas_consistency(100, 100) is False


class TestGetRuleConfidence:
    """Testa a função get_rule_confidence."""
    
    def test_known_rules(self):
        """Testa confiança de regras conhecidas."""
        assert get_rule_confidence("cc_prefix") == 0.95
        assert get_rule_confidence("casa_keyword") == 0.90
        assert get_rule_confidence("parcelas_pattern") == 0.95
    
    def test_unknown_rule(self):
        """Testa regra desconhecida retorna confiança padrão."""
        assert get_rule_confidence("unknown_rule") == 0.70


class TestRulesIntegration:
    """Testa integração entre as funções de regras."""
    
    def test_complete_card_analysis(self):
        """Testa análise completa de cartão."""
        card = "CC - CARTÃO CASA ALINE 1234"
        
        # Testa tipo
        tipo_result = infer_tipo_from_card(card)
        assert tipo_result.category == "débito"
        
        # Testa comp
        comp_result = infer_comp_from_card(card)
        assert comp_result.category == "planilha comp"
        
        # Testa titular
        titular = infer_titular_from_card(card)
        assert titular == "aline"
        
        # Testa final
        final = infer_final_cartao_from_card(card)
        assert final == "1234"
    
    def test_complete_parcelas_analysis(self):
        """Testa análise completa de parcelas."""
        desc = "Compra (3/12) PAGAMENTO 15/03/2024 na LOJA ABC"
        
        # Testa extração de parcelas
        parcelas = parse_parcelas_from_desc(desc)
        assert parcelas["no_da_parcela"] == 3
        assert parcelas["parcelas"] == 12
        
        # Testa validação
        assert validate_parcelas_consistency(3, 12) is True
        
        # Testa limpeza da descrição
        clean_desc = clean_transaction_description(desc)
        assert "PAGAMENTO" not in clean_desc
        assert "15/03/2024" not in clean_desc
        
        # Testa extração do estabelecimento
        establishment = extract_establishment_name(desc)
        assert establishment == "Na Loja Abc"  # "na" permanece como parte do texto


class TestRulesEdgeCases:
    """Testa casos extremos e edge cases."""
    
    def test_very_long_card_description(self):
        """Testa cartão com descrição muito longa."""
        long_card = "CC - CARTÃO CASA ALINE " + "1" * 100
        
        tipo_result = infer_tipo_from_card(long_card)
        assert tipo_result.category == "débito"
        
        comp_result = infer_comp_from_card(long_card)
        assert comp_result.category == "planilha comp"
    
    def test_special_characters_in_description(self):
        """Testa caracteres especiais na descrição."""
        desc = "Compra @#$% (3/12) &*() na loja!"
        
        result = parse_parcelas_from_desc(desc)
        assert result["no_da_parcela"] == 3
        assert result["parcelas"] == 12
    
    def test_unicode_characters(self):
        """Testa caracteres unicode."""
        card = "CARTÃO JOÃO 1234"
        
        result = infer_titular_from_card(card)
        assert result == "joao"
    
    def test_mixed_languages(self):
        """Testa texto em idiomas mistos."""
        desc = "Purchase (3/12) compra na loja"
        
        result = parse_parcelas_from_desc(desc)
        assert result["no_da_parcela"] == 3
        assert result["parcelas"] == 12
