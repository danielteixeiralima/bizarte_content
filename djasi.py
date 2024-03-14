def converter_data(data_str):
    """Converte uma string de data no formato 'YYYY-MM-DD' para um objeto datetime."""
    try:
        return datetime.strptime(data_str, '%Y-%m-%d')
    except ValueError:
        print(f"Erro ao converter a data: {data_str}")
        return None  # Retorna None se a conversão falhar

def converter_para_float(valor):
    if isinstance(valor, float):
        return valor
    try:
        return float(valor) if isinstance(valor, str) and valor.replace('.', '', 1).isdigit() else 0.0
    except ValueError:
        return 0.0

def converter_para_int(valor):
    if isinstance(valor, int):
        return valor
    try:
        return int(valor) if isinstance(valor, str) and valor.isdigit() else 0
    except ValueError:
        return 0

def atualizar_dados_meta_ads():
    print("Iniciando a atualização de Meta Ads...")

    # URL da API do Supermetrics
    url = "https://api.supermetrics.com/enterprise/v2/query/data/json"

    # Parâmetros da consulta
    params = {
        "ds_id": "FA",
        "ds_accounts": "list.all_accounts",
        "ds_user": "10207861565974632",
        "date_range_type": "this_year_inc",
        "fields": ("Date,adcampaign_name,adset_name,ad_name,profile,reach,"
                   "Frequency,impressions,cost,CPM,action_link_click,Clicks,"
                   "CTR,CPLC,CPC,action_subscribe"),
        "max_rows": 100000,
        "api_key": "api_JOI22IexFiXRJVdBiU_iuSZ6_2PIzonMAIdHVGWot2nF27DQB1H79BTzqJAiWRXpSu84DklqL6XsUHrlRQSgf3Nr1Nsb8pbBttsa"
    }

    print("Realizando a requisição à API...")
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Erro na requisição: Status Code {response.status_code}, Response: {response.text}")
        return

    print("Processando os dados recebidos da API...")
    data = response.json()

    if 'data' not in data:
        print("Dados não encontrados na resposta da API.")
        return

    # Cria o DataFrame com a primeira linha como cabeçalho
    df = pd.DataFrame(data['data'][1:], columns=data['data'][0])
    print(f"DataFrame criado com {len(df)} registros.")

    # Imprime as primeiras linhas do DataFrame para inspeção
    print("Primeiras linhas do DataFrame:")
    print(df.head())

    # Imprime as colunas do DataFrame
    print("Colunas do DataFrame:")
    print(df.columns)

    try:
        print("Limpando dados antigos da tabela MetaAds...")
        MetaAds.query.delete()

        print("Inserindo novos dados na tabela MetaAds...")
        for _, row in df.iterrows():
            meta_ad = MetaAds(
                date=converter_data(row['Date']),
                adcampaign_name=row['Campaign name'],
                adset_name=row['Ad set name'],
                ad_name=row['Ad name'],
                profile=row.get('Account name', None),
                reach=converter_para_int(row['Reach']),
                frequency=converter_para_float(row['Frequency']),
                impressions=converter_para_int(row['Impressions']),
                cost=converter_para_float(row['Cost']),
                cpm=converter_para_float(row['CPM (cost per 1000 impressions)']),
                action_link_click=converter_para_int(row['Link clicks']),
                clicks=converter_para_int(row['Clicks (all)']),
                ctr=converter_para_float(row['CTR (all)']),
                cplc=converter_para_float(row['CPC (cost per link click)']),
                cpc=converter_para_float(row['CPC (all)']),
                action_subscribe=converter_para_int(row['Page subscribes'])
            )
            db.session.add(meta_ad)
        db.session.commit()
        print("Dados de Meta Ads atualizados no banco de dados com sucesso.")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar o banco de dados: {e}")


# Ponto de entrada para o script, se necessário
if _name_ == "_main_":
    atualizar_dados_meta_ads()