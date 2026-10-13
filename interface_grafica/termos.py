from modulos.privacidade import VERSAO_TERMOS, DIAS_CONSERVACAO_LOGS

TERMOS_TEXTO = f"""TERMOS DE UTILIZAÇÃO DO FITCONTROL  (versão {VERSAO_TERMOS})

1. Âmbito
Estes termos aplicam-se a quem usa o FitControl para gerir a academia (administradores e funcionários). O FitControl serve para gerir alunos, planos, pagamentos, presenças, funcionários e a câmara usada no reconhecimento facial.

2. Aceitação
Para usar o sistema tem de aceitar estes termos e a Política de Privacidade. A aceitação fica registada com a data e a versão. Se os termos mudarem, é pedida uma nova aceitação no início de sessão seguinte.

3. Conta e palavra-passe
A conta é pessoal e não pode ser partilhada. As palavras-passe são guardadas cifradas e ninguém as consegue ler, nem o administrador. Avise logo a administração se suspeitar que alguém usou a sua conta. Depois de 3 tentativas falhadas o acesso fica bloqueado durante 60 segundos.

4. Dever de confidencialidade
Os dados dos alunos só podem ser consultados e usados para as tarefas da academia (inscrições, pagamentos, presenças). É proibido copiar, fotografar, exportar ou divulgar dados pessoais fora dessas tarefas.

5. Utilização correta
Não pode tentar contornar os controlos de acesso, alterar a base de dados por fora do programa nem usar a câmara para outros fins que não os previstos.

6. Registos de atividade
Para segurança, o sistema regista os inícios e fins de sessão e as operações feitas (criar, editar, eliminar, pagamentos, presenças). Estes registos ficam guardados {DIAS_CONSERVACAO_LOGS // 365} anos e são depois apagados automaticamente.

7. Pedidos dos titulares dos dados
Pedidos de acesso, correção, apagamento ou retirada de consentimento feitos pelos alunos devem ser passados ao administrador, que os trata no próprio programa (exportar dados, editar, retirar foto, apagar definitivamente) no prazo máximo de um mês.

8. Responsabilidade
Quem regista os dados é responsável pela sua exatidão. As decisões tomadas com base nos dados são da responsabilidade da academia.

9. Disponibilidade
O sistema pode ter interrupções por manutenção, atualizações ou falhas técnicas.

10. Propriedade
O programa e o seu código pertencem ao respetivo autor. Não pode ser copiado, revendido nem distribuído sem autorização.

11. Lei aplicável
Aplica-se a lei portuguesa, em especial o Regulamento Geral sobre a Proteção de Dados (Regulamento (UE) 2016/679, "RGPD") e a Lei n.º 58/2019.
"""


POLITICA_PRIVACIDADE = f"""POLÍTICA DE PRIVACIDADE  (versão {VERSAO_TERMOS})
Informação prestada nos termos dos artigos 13.º e 14.º do RGPD.

1. Responsável pelo tratamento
A entidade que explora a academia onde o FitControl está instalado, identificada na receção. Os pedidos sobre dados pessoais são feitos junto da administração da academia.

2. Que dados são tratados
Alunos: nome, telemóvel, número de documento, plano, pagamentos (valor e datas), entradas na academia (data e hora) e, só com consentimento, uma fotografia do rosto e o respetivo modelo facial.
Funcionários: nome, nome de utilizador, palavra-passe (cifrada), cargo e registos de atividade.

3. Para que servem e com que fundamento
• Gerir a inscrição, os planos e o acesso à academia: execução do contrato (art. 6.º, n.º 1, al. b).
• Registar e controlar pagamentos e emitir relatórios: execução do contrato e obrigações legais (art. 6.º, n.º 1, al. b e c).
• Reconhecimento facial para registar entradas: consentimento explícito do aluno (art. 9.º, n.º 2, al. a). É opcional; quem não consentir regista a entrada de forma manual, sem qualquer prejuízo.
• Segurança do sistema e registos de atividade: interesse legítimo da academia (art. 6.º, n.º 1, al. f).

4. Reconhecimento facial
A fotografia é tirada apenas com o consentimento do aluno, dado no momento do registo. A partir dela é calculado um modelo numérico do rosto, usado só para identificar o aluno na entrada. A câmara não grava vídeo durante o Face ID e as imagens não saem do computador. O consentimento pode ser retirado a qualquer momento: a fotografia e o modelo facial são apagados de imediato.

5. Quem tem acesso
Apenas os funcionários e administradores da academia, com conta própria. Os dados ficam guardados localmente neste computador e não são enviados para terceiros nem para fora da União Europeia.

6. Durante quanto tempo
• Dados do aluno: enquanto a inscrição estiver ativa. Quando é eliminado vai para um arquivo e é apagado definitivamente ao fim de 60 dias (ou antes, a pedido).
• Pagamentos: pelo prazo exigido pela legislação fiscal e contabilística.
• Registos de presenças e de atividade: {DIAS_CONSERVACAO_LOGS // 365} anos, sendo depois apagados automaticamente.
• Fotografia e modelo facial: até o consentimento ser retirado ou o aluno ser eliminado.

7. Direitos dos titulares
Qualquer aluno ou funcionário pode pedir acesso aos seus dados (incluindo cópia em formato digital), retificação, apagamento, limitação do tratamento, portabilidade e oposição, bem como retirar o consentimento, sem afetar a licitude do tratamento feito antes. Os pedidos são respondidos no prazo de um mês.
Tem ainda o direito de apresentar reclamação à Comissão Nacional de Proteção de Dados (CNPD), www.cnpd.pt.

8. Segurança
Acesso por utilizador e palavra-passe cifrada, bloqueio após tentativas falhadas, permissões diferentes para funcionários e administradores, confirmação por palavra-passe nas operações irreversíveis e registo das operações feitas.

9. Alterações
Esta política pode ser atualizada. A versão em vigor é sempre a apresentada no programa.
"""


CONSENTIMENTO_FACIAL = (
    "O aluno autoriza a recolha de uma fotografia do rosto e do respetivo modelo facial, "
    "usados apenas para registar as entradas na academia. É opcional e pode ser retirado "
    "a qualquer momento (art. 9.º, n.º 2, al. a) do RGPD)."
)
