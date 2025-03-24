from django.shortcuts import render
from .config import *
# Create your views here.
def home_view(request):
    return render(request, "pages/home.html")


def TFG_calculadora(idade, sexo, etnia, creatinina):
    """
    Cálculo da Taxa de Filtração Glomerular (TFG) utilizando a fórmula CKD-EPI 2009.

    Parâmetros:
      creatinina (float):  Creatinina sérica em mg/dL.
      idade (int):         Idade do paciente em anos.
      sexo (str):          Sexo masculino ou feminino.
      etnia (int):         Etnia branca, preta, parda, amarela, indigena.

    Retorno: 
        eGFR (float): TFG estimada em mL/min/1.73m².

     Fórmula CKD-EPI:
      Para homens:
        Se creatinina ≤ 0.9:
          eGFR = 141 * (creatinina/0.9)^(-0.411) * (0.993)^idade
        Se creatinina > 0.9:
          eGFR = 141 * (creatinina/0.9)^(-1.209) * (0.993)^idade

      Para mulheres:
        Se creatinina ≤ 0.7:
          eGFR = 141 * 1.018 * (creatinina/0.7)^(-0.329) * (0.993)^idade
        Se creatinina > 0.7:
          eGFR = 141 * 1.018 * (creatinina/0.7)^(-1.209) * (0.993)^idade    
      Se o paciente for negro ou pardo, multiplica o resultado por 1.159.
    """
    multiplicador_etnia = 1.159 if etnia.lower() in ['preto', 'pardo'] else 1

    if sexo.lower() == 'masculino':
        if creatinina <= 0.9:
            k = -0.411    
        else:
            k = -1.209
        egfr = 141 * (creatinina / 0.9) ** k * (0.993) ** idade
    
    else:
        if creatinina <= 0.7:
            k = -0.329
        else:
            k = -1.209
        egfr = 141 * 1.018 * (creatinina / 0.9) ** k * (0.993) ** idade 
    
    egfr *= multiplicador_etnia        

    return egfr


def diagnostico_EGFR(egfr):
    """
        Classificação do estágio da função renal baseado no intervalo da TFG estimada

        Parâmetro:
            egfr (float): TFG estimada

         Estágios    Diagnóstico               Intervalos
            G1   ->  Normal                    (> 90 mL/min/1.73m²)
            G2   ->  Redução Discreta          (89-60 mL/min/1,73m²)
            G3a  ->  Redução Discreta-Moderada (59-45 mL/min/1,73m²)
            G3b  ->  Redução Discreta-Severa   (44-30 mL/min/1,73m²)
            G4   ->  Redução Severa            (29-15 mL/min/1,73m²)
            G5   ->  Falência Renal            (<15 mL/min/1,73m²)
    """
    if egfr > 90:
        return {"Estagio": "G1", "Diagnostico": "Normal", "cor": "#4CAF50"}
    elif 60 <= egfr <= 89:
        return {"Estagio": "G2", "Diagnostico": "Redução Discreta", "cor": "#8BC34A"}
    elif 45 <= egfr <= 59:
        return {"Estagio": "G3a", "Diagnostico": "Redução Discreta-Moderada", "cor": "#FFEB3B"}
    elif 30 <= egfr <= 44:
        return {"Estagio": "G3b", "Diagnostico": "Redução Discreta-Severa", "cor": "#FF9800"}
    elif 15 <= egfr <= 29:
        return {"Estagio": "G4", "Diagnostico": "Redução Severa", "cor": "#FF5722"}
    else:
        return {"Estagio": "G5", "Diagnostico": "Falência Renal", "cor": "#F44336"}

def TFG_view(request):
    """
    Processa requisições para o cálculo da Taxa de Filtração Glomerular (TFG).

    - Se o método for POST, obtém os dados do formulário:
      - idade
      - sexo
      - etnia
      - creatinina
      e calcula a TFG, gerando um diagnóstico.

    - Se o método for GET, apenas renderiza a página sem calcular a TFG.
    """
    resultado = None
    if request.method == 'POST':
        idade = int(request.POST.get("idade"))
        sexo = request.POST.get("sexo")
        etnia = request.POST.get("etnia")
        creatinina = float(request.POST.get("creatinina"))
        egfr = TFG_calculadora(idade, sexo, etnia, creatinina)
        resultado = diagnostico_EGFR(egfr)
    return render(request, "pages/tfg.html", {"resultado": resultado}) 



def calcula_risco_percentual(pontuacao, sexo):
    """
    Calcula o risco percentual com base na pontuação e no sexo do paciente.

    - Se o sexo for "feminino":
      - Para pontuações menores ou iguais a -2, o risco é 0.90%.
      - Para pontuações iguais ou superiores a 21, o risco é 30.1%.
      - Caso contrário, utiliza a tabela `porcentagem_risco_global_mulheres`.

    - Se o sexo for diferente de "feminino" (assumindo masculino):
      - Para pontuações menores ou iguais a -3, o risco é 0.90%.
      - Para pontuações iguais ou superiores a 18, o risco é 30.1%.
      - Caso contrário, utiliza a tabela `porcentagem_risco_global_homens`.

    Retorna o risco percentual correspondente à pontuação e ao sexo do paciente.
    """
    if sexo == "feminino":
        if pontuacao <= -2:
            risco = 0.90
        elif pontuacao >= 21:
            risco = 30.1
        else:
            risco = porcentagem_risco_global_mulheres[pontuacao]
    else:
        if pontuacao <= -3:
            risco = 0.90
        elif pontuacao >= 18:
            risco = 30.1
        else:
            risco = porcentagem_risco_global_homens[pontuacao]

    return risco

def calcula_risco_cardiovascular(idade, sexo, hdl, colesterol, pas, pas_tratada, diabetes, fumante):
    """
    Calcula a pontuação de risco cardiovascular com base em diversos fatores clínicos e demográficos.

    Parâmetros:
    - 'idade' (int): Idade do paciente.
    - 'sexo' (str): "feminino" ou "masculino".
    - 'hdl' (float): Nível de HDL (colesterol bom) em (mg/dL).
    - 'colesterol' (float): Nível total de colesterol em (mg/dL).
    - 'pas' (int): Pressão arterial sistólica em (mm/Hg).
    - 'pas_tratada' (bool): Indica se o paciente está sob tratamento para hipertensão.
    - 'fumante' (bool): Indica se o paciente é fumante.
    - 'diabetes' (bool): Indica se o paciente tem diabetes.

    Lógica de Cálculo:
    **Definição das tabelas**  
    - Usa diferentes tabelas de pontuação para homens e mulheres.
    - Cada fator contribui com uma pontuação baseada em faixas de valores.


   **Cálculo do risco percentual**  
   - A pontuação final é convertida em um percentual de risco por meio da função `calcula_risco_percentual()`.  
  
   **Classificação do risco**  
   - Risco Baixo: Percentual < 5%.  
   - Risco Intermediário: Percentual entre 5% e 10% (mulheres) ou entre 5% e 20% (homens).  
   - Risco Alto: Percentual acima desses limites.  

   Retorno:
   - Dicionário contendo a classificação do risco e o percentual correspondente.
    """
    pontuacao = 0
    if sexo == "feminino":
        idades_tabela = tabela_pontos_risco_global_mulheres.get("idade")
        hdl_tabela = tabela_pontos_risco_global_mulheres.get("hdl")
        colesterol_tabela = tabela_pontos_risco_global_mulheres.get("colesterol")
        pas_tabela = tabela_pontos_risco_global_mulheres.get("pasT") if pas_tratada else tabela_pontos_risco_global_mulheres.get("pasNT")
        
        if idade >= 75:
            pontuacao += 15
        else:
            for pontos, intervalo_idade in idades_tabela.items():
                if intervalo_idade[0] <= idade <= intervalo_idade[1]:
                    pontuacao += pontos
                    break

        if hdl >= 60:
            pontuacao += -2
            
        else:
            for pontos, intervalo_hdl in hdl_tabela.items():
                if intervalo_hdl[0] <= hdl <= intervalo_hdl[1]:
                    pontuacao += pontos
                    break          
        if colesterol >= 280:
            pontuacao += 5
        else:
            for pontos, intervalo_colesterol in colesterol_tabela.items():
                if intervalo_colesterol[0] <= colesterol <= intervalo_colesterol[1]:
                    pontuacao += pontos
                    break
        if pas >= 160:
            if pas_tratada:
                pontuacao += 7
            else:
                pontuacao += 5
        else:
            for pontos, intervalo_pas in pas_tabela.items():
                if intervalo_pas[0] <= pas <= intervalo_pas[1]:
                    pontuacao += pontos
                    break
        print("pas pot: ", pontuacao)            
        

        #3 pontos se for fumante senão 0 
        pontuacao += 3 if fumante else 0
        #4 pontos se for diabetico senão 0
        pontuacao += 4 if diabetes else 0
    else: #se for homem
        if sexo == "masculino":
            idades_tabela = tabela_pontos_risco_global_homens.get("idade")
            hdl_tabela = tabela_pontos_risco_global_homens.get("hdl")
            colesterol_tabela = tabela_pontos_risco_global_homens.get("colesterol")
            pas_tabela = tabela_pontos_risco_global_homens.get("pasT") if pas_tratada else tabela_pontos_risco_global_homens.get("pasNT")

            if idade >= 75:
                pontuacao += 15
            else:
                for pontos, intervalo_idade in idades_tabela.items():
                    if intervalo_idade[0] <= idade <= intervalo_idade[1]:
                        pontuacao += pontos
                        break
            print("idade: ", pontuacao)            
            if hdl >= 60:
                pontuacao += -2
            else:
                for pontos, intervalo_hdl in hdl_tabela.items():
                    if intervalo_hdl[0] <= hdl <= intervalo_hdl[1]:
                        pontuacao += pontos
                        break
            print("hdl: ", pontuacao)            
            if colesterol >= 280:
                pontuacao += 4
            else:
                for pontos, intervalo_colesterol in colesterol_tabela.items():
                    if intervalo_colesterol[0] <= colesterol <= intervalo_colesterol[1]:
                        pontuacao += pontos
                        break
            print("colesterol: ", pontuacao)            
            if pas >= 160:
                if pas_tratada:
                    pontuacao += 5
                else:
                    pontuacao += 3
            else:
                for pontos, intervalo_pas in pas_tabela.items():
                    if intervalo_pas[0] <= pas <= intervalo_pas[1]:
                        pontuacao += pontos
                        break

            print("pas: ", pontuacao)           
            #3 pontos se for fumante senão 0 
            pontuacao += 4 if fumante else 0
            print("fumante: ", pontuacao)
            #4 pontos se for diabetico senão 0
            pontuacao += 3 if diabetes else 0
            print("diabetes ", pontuacao)

    percentual_risco_cardiovascular = calcula_risco_percentual(pontuacao, sexo)  
    
    if percentual_risco_cardiovascular < 5:
        return {"classificacao": "Risco Baixo.", "percentual": percentual_risco_cardiovascular}
    elif (percentual_risco_cardiovascular < 10 and sexo == "feminino") or (percentual_risco_cardiovascular < 20 and sexo == "masculino"):
        return {"classificacao": "Risco Intermediário.", "percentual": percentual_risco_cardiovascular}
    else:
        return {"classificacao": "Risco Alto.", "percentual": percentual_risco_cardiovascular}

#CRC - Calculadora Risco Cardiovascular
def CRC_view(request):
    """
    Processa requisições para o cálculo de Risco Cardiovascular.

    - Se o método for POST, obtém os dados do formulário:
      - idade
      - sexo
      - colesterol total em (mg/dL)
      - hdl em (mg/dL)
      - pas (Pressão Arterial Sistólica) em (mm/Hg)
      - pas Tratada
      - fumante 
      - diabetes

    - Se o método for GET, apenas renderiza a página sem calcular o risco cardiovascular.
    """
    resultado = None
    if request.method == "POST":
        idade = int(request.POST.get("idade"))
        sexo = request.POST.get("sexo")
        colesterol_total = float(request.POST.get("colesterol-total"))
        hdl = float(request.POST.get("hdl")) 
        pas = float(request.POST.get("pas")) 
        pas_tratada = True if request.POST.get("pas-tratada") == "true" else False
        fumante = True if request.POST.get("fumante") == "true" else False 
        diabetes = True if request.POST.get("diabetes") == "true" else False
        
        resultado = calcula_risco_cardiovascular(idade, sexo, hdl, colesterol_total, pas, pas_tratada, diabetes, fumante)
        
    return render(request, "pages/crc.html", {"resultado": resultado})
    