import requests
from models import db, InstagramData
from datetime import datetime

def parse_date(date_string):
    try:
        return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        print(f"Data inválida: {date_string}")
        return None

def consulta_api_e_salva_db():
    base_url = "https://api.supermetrics.com/enterprise/v2/query/data/json?json="
    payload = {
        "ds_id": "IGI",
        "ds_accounts": "17841401436043308,17841434836792722,17841401205584271,17841403310433082,17841403472028515,17841453160750668,17841402378506364,17841414458783653,17841445387902952,17841400549992762,17841401949171267,17841405356255775,17841446008023776,17841401503890002,17841401398820634,17841401737082506,17841400093508513,17841446395973832,17841404143391185,17841411869370600,17841404033286688,17841450814944437,17841401307160100",  # Lista de contas
        "ds_user": "10209474877426410",
        "date_range_type": "this_year_inc",
        "fields": "account_id,dataSourceName,ig_id,media_caption,media_id,media_permalink,media_shortcode,media_thumbnail_url,media_type,media_url,name,timestamp,today,username,website,media_carousel_album_engagement,media_carousel_album_impressions,media_carousel_album_reach,media_carousel_album_saved,media_comments_count,media_engagement,media_impressions,media_like_count,media_reach,media_saved,media_story_exits,media_story_impressions,media_story_reach,media_story_replies,media_story_taps_back,media_story_taps_forward,media_video_views",  # Lista de campos
        "max_rows": 100000,
        "api_key": "api_JOI22IexFiXRJVdBiU_iuSZ6_2PIzonMAIdHVGWot2nF27DQB1H79BTzqJAiWRXpSu84DklqL6XsUHrlRQSgf3Nr1Nsb8pbBttsa"
    }

    # Lógica de paginação
    next_page_token = None
    while True:
        if next_page_token:
            # Atualize a URL ou parâmetros aqui para incluir o token da próxima página
            # A lógica exata dependerá de como a API implementa a paginação
            payload['page_token'] = next_page_token

        response = requests.get(base_url, params=payload)
        if response.status_code != 200:
            print(f"Falha na requisição: Status code {response.status_code}")
            break

        data = response.json()

    # Verifique se 'data' é uma chave e contém uma lista
    if 'data' not in data or not isinstance(data['data'], list):
        print("A resposta da API não contém a chave 'data' ou não é uma lista.")
        return

    # Processar cada item da lista
    for item_list in data['data']:
        if not isinstance(item_list, list):
            print("Item não é uma lista.")
            continue
        if len(item_list) < 32:  # Certifique-se de que a lista tenha o número esperado de elementos
            print("A lista não contém elementos suficientes.")
            continue

        # Verifique se o registro já existe
        if InstagramData.query.filter_by(instagram_id=str(item_list[2])).first():
            print(f"Registro com instagram_id {item_list[2]} já existe.")
            continue

        # Mapear os elementos da lista para os campos da classe InstagramData
        novo_dado = InstagramData(
            profile_id=item_list[0],
            data_source=item_list[1],
            instagram_id=str(item_list[2]),  # Convertendo para string, caso necessário
            media_caption=item_list[3],
            media_id=item_list[4],
            media_permalink=item_list[5],
            media_shortcode=item_list[6],
            video_thumbnail_url=item_list[7],
            media_type=item_list[8],
            media_url=item_list[9],
            name=item_list[10],
            media_created=parse_date(item_list[11]),
            today=parse_date(item_list[12]),
            username=item_list[13],
            website=item_list[14],
            carousel_album_engagement=item_list[15],
            carousel_album_impressions=item_list[16],
            carousel_album_reach=item_list[17],
            carousel_album_saved=item_list[18],
            comments_count=item_list[19],
            engagement=item_list[20],
            media_impressions=item_list[21],
            like_count=item_list[22],
            media_reach=item_list[23],
            unique_saves=item_list[24],
            story_exits=item_list[25],
            story_impressions=item_list[26],
            story_reach=item_list[27],
            story_replies=item_list[28],
            taps_back=item_list[29],
            taps_forward=item_list[30],
            video_views=item_list[31]
        )

        # Adicionando o novo objeto à sessão do banco de dados
        db.session.add(novo_dado)

    # Confirmando as inserções
    try:
        db.session.commit()
        print("Dados inseridos com sucesso.")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao inserir dados: {e}")