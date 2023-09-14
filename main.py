import requests
import json
import string
import random
import openai

url = 'https://sdw-2023-prd.up.railway.app/users'
openai.api_key = 'minha_chave_aqui'
lista_meus_ids = []

def obter_lista_ids_numbers(url): # Obtendo os identificadores únicos para inserir novos usuários no POST
    
    try:
        resposta_url = requests.get(url)
        resposta_url.raise_for_status()  # Exceção se a resposta não for bem-sucedida
        resposta_json = resposta_url.json()
        
        lista_ID_user = sorted([item.get('id') for item in resposta_json if 'id' in item])
        lista_ID_conta = sorted([item['account']['id'] for item in resposta_json if 'account' in item and 'id' in item['account']])
        lista_ID_cartao = sorted([item['card']['id'] for item in resposta_json if 'card' in item and 'id' in item['card']])
        lista_number_conta = [item['account']['number'] for item in resposta_json if 'account' in item and 'number' in item['account']]
        lista_number_cartao = [item['card']['number'] for item in resposta_json if 'card' in item and 'number' in item['card']]
        
        return {
            'lista_ID_user': lista_ID_user,
            'lista_ID_conta': lista_ID_conta,
            'lista_ID_cartao': lista_ID_cartao,
            'lista_number_conta': lista_number_conta,
            'lista_number_cartao': lista_number_cartao
        }
    except requests.exceptions.RequestException as e:
        print(f"A requisição falhou com o código de status: {e}")
        return {}

def gera_aleatoria(lista, tamanho=8): # Gerando os números para conta e cartão de crédito
    
    while True:
        nova_string = ''.join(random.choices(string.digits, k=tamanho))
        if nova_string not in lista:
            return nova_string

def gera_valor(): # Gerando valores flutuantes para limite de conta e cartão
    return random.uniform(100.0, 5000.0)

def set_novos_ids(lista_ids, url): # POST nos novos usuários com os valores gerados pelas funções gera_aleatoria() e gera_valor()
    
    if not lista_ids:
        print("Listas de números vazias. Não é possível gerar números aleatórios.")
        return
    
    novo_id_user = lista_ids['lista_ID_user'][-1] + 1
    novo_id_conta = lista_ids['lista_ID_conta'][-1] + 1
    novo_id_cartao = lista_ids['lista_ID_cartao'][-1] + 1

    lista_number_conta = lista_ids['lista_number_conta']
    lista_number_cartao = lista_ids['lista_number_cartao']

    novo_numero_conta = gera_aleatoria(lista_number_conta)
    novo_numero_cartao = gera_aleatoria(lista_number_cartao)

    novo_objeto = {
        "id": novo_id_user,
        "name": f"Pythao teste: {novo_id_user}",
        "account": {
            "id": novo_id_conta,
            "number": novo_numero_conta,
            "agency": "1526",
            "balance": 0.00,
            "limit": gera_valor()
        },
        "card": {
            "id": novo_id_cartao,
            "number": novo_numero_cartao,
            "limit": gera_valor()
        },
        "features": [],
        "news": []
    }
    
    try:
        resposta_json = requests.post(url, json=novo_objeto)
        resposta_json.raise_for_status()

        if resposta_json.status_code == 201:
            print(f"Novo ID {novo_id_user} criado com sucesso!")
            return novo_id_user
        else:
            print(f"Falha ao criar o novo ID. Código de status: {resposta_json.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer a solicitação POST: {e}")

def filtrar_usuario(url, lista_meus_ids): # Filtrando apenas os usuários criados agora com limite de cartão entre 1000.00 e 3000.00 e que news esteja vazio (minha regra de negócio)
    try:
        resposta_json = requests.get(url)
        resposta_json.raise_for_status()

        if resposta_json.status_code == 200:
           
            parse_json = resposta_json.json()
            filtrar_resposta = filter(lambda user: user['id'] in lista_meus_ids and user['card']['limit'] is not None and 1000 <= user['card']['limit'] <= 3000 and not user['news'], parse_json)
            
            return list(filtrar_resposta)
            
        else:
            print(f"Falha. Código de status: {resposta_json.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer a solicitação GET: {e}")

def chat_gpt(): # Conexão com a API do chatGPT e solicitação de um conselho financeiro
    
    try:
        
        # Prompt para o conselho
        prompt = f"Uma frase com um bom conselho financeiro"

        # Faz a solicitação à API do ChatGPT
        resposta = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            max_tokens=50,
            n=1,
            stop=None,
            temperature=0.7
        )
        
        # Extrai o conselho da resposta     
        return resposta.choices[0].text.strip('\"')

    except Exception as e:
        print(f"Erro ao traduzir a palavra: {e}")
        return None

def conselho_gpt(primeiros_exemplos): # Recebendo conselhos do GPT e atualizando a tag news do usuário pelo método PUT
  # Conselhos GPT
  try:
      
      for user in primeiros_exemplos:
          
          user['news'] = [{'description': chat_gpt()}] # adicionando novo valor a news
          
          response = requests.put(f'{url}/{user["id"]}', json = user) # adicionando novo valor a news do user de id x
          response.raise_for_status()
  
          if response.status_code == 200:
              print(f"ID {user['id']} atualizado com sucesso!")
          else:
              print(f"Falha ao atualizar o ID {user['id']}. Código de status: {response.status_code}")
  
  except requests.exceptions.RequestException as e:
      print(f"Erro ao fazer a solicitação: {e}")

for i in range(1, 4): # Pelo chatGPT aceitar apenas três requisições por minuto de modo gratuito, decidi gerar apenas 3 novos usuários para carater de teste
  
    lista_ids = obter_lista_ids_numbers(url)  # Lista para não repetir e retonar erro no POST
    novo_ID = set_novos_ids(lista_ids, url) # Adicionando em uma lista todos os ids criados
    lista_meus_ids.append(novo_ID)

conselho_gpt(filtrar_usuario(url, lista_meus_ids))  # Duas funções: filtrar_usuario -> Retorna os usuários filtrados para serem atualizados conselho_gpt -> Responsável por fazer o PUT nos usuários

