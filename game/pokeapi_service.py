import requests
from .models import Pokemon
import time


# タイプの日本語マッピング
TYPE_MAPPING = {
    'normal': 'ノーマル', 'fire': 'ほのお', 'water': 'みず', 'electric': 'でんき',
    'grass': 'くさ', 'ice': 'こおり', 'fighting': 'かくとう', 'poison': 'どく',
    'ground': 'じめん', 'flying': 'ひこう', 'psychic': 'エスパー', 'bug': 'むし',
    'rock': 'いわ', 'ghost': 'ゴースト', 'dragon': 'ドラゴン', 'dark': 'あく',
    'steel': 'はがね', 'fairy': 'フェアリー'
}


def get_generation_from_id(pokemon_id):
    """ポケモンIDから世代を判定"""
    if pokemon_id <= 151:
        return 1
    elif pokemon_id <= 251:
        return 2
    elif pokemon_id <= 386:
        return 3
    elif pokemon_id <= 493:
        return 4
    elif pokemon_id <= 649:
        return 5
    elif pokemon_id <= 721:
        return 6
    elif pokemon_id <= 809:
        return 7
    elif pokemon_id <= 905:
        return 8
    else:
        return 9


def get_evolution_count(evolution_chain_url):
    """進化チェーンから進化回数を取得"""
    try:
        response = requests.get(evolution_chain_url, timeout=10)
        if response.status_code != 200:
            return 0
        
        chain_data = response.json()
        
        def count_evolutions(chain, current_count=0):
            """再帰的に進化回数をカウント"""
            if not chain.get('evolves_to'):
                return current_count
            
            # 最も長い進化チェーンを返す
            max_count = current_count
            for evolution in chain['evolves_to']:
                count = count_evolutions(evolution, current_count + 1)
                max_count = max(max_count, count)
            
            return max_count
        
        return count_evolutions(chain_data['chain'])
    
    except Exception as e:
        print(f"進化チェーン取得エラー: {e}")
        return 0


def fetch_pokemon_data(pokemon_id):
    """PokeAPIから単一ポケモンのデータを取得"""
    try:
        # 基本データ取得
        pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
        response = requests.get(pokemon_url, timeout=10)
        
        if response.status_code != 200:
            return None
        
        pokemon_data = response.json()
        
        # 種族データ取得（日本語名と進化チェーン用）
        species_url = pokemon_data['species']['url']
        species_response = requests.get(species_url, timeout=10)
        
        if species_response.status_code != 200:
            return None
        
        species_data = species_response.json()
        
        # 日本語名を取得
        name_ja = None
        for name_entry in species_data['names']:
            if name_entry['language']['name'] == 'ja':
                name_ja = name_entry['name']
                break
        
        if not name_ja:
            name_ja = pokemon_data['name']
        
        # タイプ取得
        types = pokemon_data['types']
        type1 = TYPE_MAPPING.get(types[0]['type']['name'], types[0]['type']['name'])
        type2 = None
        if len(types) > 1:
            type2 = TYPE_MAPPING.get(types[1]['type']['name'], types[1]['type']['name'])
        
        # 進化回数取得
        evolution_chain_url = species_data['evolution_chain']['url']
        evolution_count = get_evolution_count(evolution_chain_url)
        
        # 世代判定
        generation = get_generation_from_id(pokemon_id)
        
        return {
            'pokedex_number': pokemon_id,
            'name_ja': name_ja,
            'name_en': pokemon_data['name'],
            'type1': type1,
            'type2': type2,
            'height': pokemon_data['height'] / 10,  # デシメートルをメートルに変換
            'weight': pokemon_data['weight'] / 10,  # ヘクトグラムをキログラムに変換
            'generation': generation,
            'evolution_count': evolution_count,
        }
    
    except Exception as e:
        print(f"ポケモンID {pokemon_id} のデータ取得エラー: {e}")
        return None


def init_pokemon_data(max_pokemon=151):
    """PokeAPIからポケモンデータを取得してデータベースに保存"""
    print(f"ポケモンデータの初期化を開始します（最大{max_pokemon}匹）...")
    
    success_count = 0
    error_count = 0
    
    for pokemon_id in range(1, max_pokemon + 1):
        # 既に存在する場合はスキップ
        if Pokemon.objects.filter(pokedex_number=pokemon_id).exists():
            print(f"No.{pokemon_id:04d} は既に登録済みです")
            success_count += 1
            continue
        
        print(f"No.{pokemon_id:04d} を取得中...")
        pokemon_data = fetch_pokemon_data(pokemon_id)
        
        if pokemon_data:
            try:
                Pokemon.objects.create(**pokemon_data)
                print(f"✓ No.{pokemon_id:04d} {pokemon_data['name_ja']} を登録しました")
                success_count += 1
            except Exception as e:
                print(f"✗ No.{pokemon_id:04d} の登録に失敗: {e}")
                error_count += 1
        else:
            print(f"✗ No.{pokemon_id:04d} のデータ取得に失敗しました")
            error_count += 1
        
        # API負荷軽減のため少し待機
        time.sleep(0.5)
    
    print(f"\n初期化完了: 成功 {success_count}匹, 失敗 {error_count}匹")
    return success_count, error_count
