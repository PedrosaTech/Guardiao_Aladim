# 📄 Impressão de NF-e em PDF - Layout SEFAZ-BA

## ✅ Implementação Completa

### Funcionalidades Implementadas

1. **Geração de PDF da NF-e**
   - Layout seguindo padrão SEFAZ-BA
   - Template HTML/CSS responsivo
   - Conversão para PDF usando WeasyPrint

2. **View de Impressão**
   - URL: `/fiscal/nfe/<nota_id>/pdf/`
   - Protegida com `@login_required`
   - Gera PDF e retorna para download/visualização

3. **Integração com Admin**
   - Botão "Imprimir NF-e (PDF)" na página de edição da nota
   - Template customizado do admin

## 📋 Arquivos Criados/Modificados

### Novos Arquivos
- `fiscal/views.py` - View para gerar PDF
- `fiscal/urls.py` - URLs do módulo fiscal
- `templates/fiscal/nfe_pdf.html` - Template HTML da NF-e
- `templates/admin/fiscal/notafiscalsaida/change_form.html` - Template customizado do admin

### Arquivos Modificados
- `requirements.txt` - Adicionado weasyprint
- `guardiao_aladin/urls.py` - Incluído fiscal.urls
- `fiscal/admin.py` - Adicionado botão de impressão

## 🔧 Instalação

### 1. Instalar WeasyPrint

```bash
pip install weasyprint
```

**Nota:** WeasyPrint requer algumas dependências do sistema. No WSL/Linux:

```bash
sudo apt-get update
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0
```

### 2. Verificar Instalação

```bash
python manage.py check
```

## 🎨 Layout da NF-e

O template segue o layout padrão SEFAZ-BA com:

- **Cabeçalho SEFAZ**
  - Título "NOTA FISCAL ELETRÔNICA"
  - Número e série
  - Chave de acesso formatada
  - Status da nota

- **Informações da NF-e**
  - Data de emissão
  - Natureza da operação
  - Forma de pagamento

- **Emitente e Destinatário**
  - Dados completos da empresa/loja
  - Dados completos do cliente
  - Endereços formatados

- **Itens da Nota**
  - Tabela com todos os itens do pedido
  - Código, descrição, NCM, CFOP
  - Quantidade, preço unitário, total

- **Cálculo do Imposto**
  - Base de cálculo ICMS
  - Valores de impostos
  - Valor total da NF-e

- **Rodapé**
  - Chave de acesso completa
  - Placeholder para QR Code
  - Links para consulta SEFAZ

## 🚀 Como Usar

### 1. Via Admin

1. Acesse o admin: `/admin/fiscal/notafiscalsaida/`
2. Clique em uma NF-e para editar
3. Na parte inferior, clique em "📄 Imprimir NF-e (PDF)"
4. O PDF será gerado e aberto no navegador

### 2. Via URL Direta

```
http://localhost:8000/fiscal/nfe/<nota_id>/pdf/
```

### 3. Via Código

```python
from django.urls import reverse
from django.shortcuts import redirect

# Redirecionar para impressão
url = reverse('fiscal:imprimir_nfe_pdf', args=[nota.id])
return redirect(url)
```

## 📝 Template HTML

O template `templates/fiscal/nfe_pdf.html` contém:

- CSS inline para impressão
- Layout responsivo (A4)
- Formatação seguindo padrão SEFAZ
- Dados dinâmicos do Django

### Personalização

Para ajustar o layout, edite:
- `templates/fiscal/nfe_pdf.html` - HTML e CSS
- Cores, fontes, espaçamentos podem ser ajustados no CSS

## 🔍 Estrutura do PDF

```
┌─────────────────────────────────┐
│  CABEÇALHO SEFAZ                │
│  (Título, Número, Chave)        │
├─────────────────────────────────┤
│  INFORMAÇÕES DA NF-e            │
│  (Data, Natureza, Pagamento)    │
├─────────────────────────────────┤
│  EMITENTE    │  DESTINATÁRIO    │
│  (Empresa)   │  (Cliente)       │
├─────────────────────────────────┤
│  ITENS DA NOTA                  │
│  (Tabela com produtos)          │
├─────────────────────────────────┤
│  CÁLCULO DO IMPOSTO             │
│  (Totais e impostos)            │
├─────────────────────────────────┤
│  RODAPÉ                         │
│  (Chave, QR Code, Links)        │
└─────────────────────────────────┘
```

## ⚠️ Observações

1. **WeasyPrint**: Requer instalação e dependências do sistema
2. **Chave de Acesso**: Se não houver, mostra "A ser gerada após autorização"
3. **QR Code**: Placeholder até integração com SEFAZ
4. **Itens**: Se não houver pedido, mostra "Nenhum item cadastrado"

## 🎯 Próximos Passos

1. **Integração SEFAZ Real**
   - Gerar chave de acesso real
   - Gerar QR Code real
   - Validar XML antes de imprimir

2. **Melhorias**
   - Adicionar logo da empresa
   - Personalizar cores
   - Adicionar informações adicionais

3. **NFC-e**
   - Criar template similar para NFC-e
   - Layout simplificado para balcão

## ✅ Status

- ✅ Template HTML criado
- ✅ View de impressão implementada
- ✅ Integração com admin
- ✅ Layout SEFAZ-BA
- ⏳ Aguardando instalação do weasyprint

