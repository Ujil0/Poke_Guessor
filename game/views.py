#ビューを定義する
from django.shortcuts import render #htmlを表示する
from django.http import JsonResponse #ブラウザに対してJSON形式のデータを返す。画面の変化にリロードさせる必要がない。
from django.views.decorators.csrf import csrf_exempt#CSRF対策。できれば辞めたい
from .models import Pokemon, GameSession, PlayerStats #models.pyで定義したモデルをインポート
import json #JSON形式のデータを扱う
import random #ランダムな数値を生成する
import uuid #UUID(不変で重複しない識別子)を生成する


def index(request):
    """メインゲーム画面"""
    return render(request, 'game/index.html')


def get_or_create_player_id(request):
    """クッキーからプレイヤーIDを取得、なければ新規作成"""
    player_id = request.COOKIES.get('player_id')
    if not player_id:
        player_id = str(uuid.uuid4())
    return player_id


@csrf_exempt
def start_game(request):
    """新しいゲームを開始"""
    if request.method != 'POST':#メソッドがPOSTじゃなければエラーを返す
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    # プレイヤーID取得
    player_id = get_or_create_player_id(request)
    
    # ランダムにポケモンを選択
    """データベースの中にポケモンが登録されているか確認"""
    pokemon_count = Pokemon.objects.count()
    if pokemon_count == 0:
        return JsonResponse({'error': 'ポケモンデータが登録されていません'}, status=500)
    
    random_pokemon = Pokemon.objects.order_by('?').first()
    
    # ゲームセッション作成
    session = GameSession.objects.create(
        player_id=player_id,
        target_pokemon=random_pokemon
    )
    
    response = JsonResponse({
        'session_id': str(session.session_id),
        'message': 'ゲームを開始しました！'
    })
    
    # クッキーにプレイヤーIDを保存
    response.set_cookie('player_id', player_id, max_age=365*24*60*60)  # 1年間有効
    
    return response


@csrf_exempt
def guess_pokemon(request):
    """ポケモンを推測"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        pokemon_name = data.get('pokemon_name')
        
        if not session_id or not pokemon_name:
            return JsonResponse({'error': 'session_idとpokemon_nameが必要です'}, status=400)
        
        # セッション取得
        try:
            session = GameSession.objects.get(session_id=session_id, status='playing')
        except GameSession.DoesNotExist:
            return JsonResponse({'error': 'セッションが見つかりません'}, status=404)
        
        # 推測したポケモンを取得
        try:
            guessed_pokemon = Pokemon.objects.get(name_ja=pokemon_name)
        except Pokemon.DoesNotExist:
            return JsonResponse({'error': 'ポケモンが見つかりません'}, status=404)
        
        # 試行回数を増やす
        session.attempts += 1
        session.save()
        
        target = session.target_pokemon
        
        # 比較結果を作成
        result = {
            'name': guessed_pokemon.name_ja,
            'name_match': guessed_pokemon.name_ja == target.name_ja,
            'pokedex_number': guessed_pokemon.pokedex_number,
            'pokedex_match': 'match' if guessed_pokemon.pokedex_number == target.pokedex_number else ('up' if guessed_pokemon.pokedex_number < target.pokedex_number else 'down'),
            'type1': guessed_pokemon.type1,
            'type2': guessed_pokemon.type2 or '',
            'type_match': compare_types(guessed_pokemon, target),
            'height': guessed_pokemon.height,
            'height_match': 'match' if guessed_pokemon.height == target.height else ('up' if guessed_pokemon.height < target.height else 'down'),
            'weight': guessed_pokemon.weight,
            'weight_match': 'match' if guessed_pokemon.weight == target.weight else ('up' if guessed_pokemon.weight < target.weight else 'down'),
            'generation': guessed_pokemon.generation,
            'generation_match': 'match' if guessed_pokemon.generation == target.generation else 'mismatch',
            'evolution_count': guessed_pokemon.evolution_count,
            'evolution_match': 'match' if guessed_pokemon.evolution_count == target.evolution_count else 'mismatch',
            'attempts': session.attempts,
        }
        
        # 正解判定
        if guessed_pokemon.name_ja == target.name_ja:
            session.status = 'cleared'
            session.save()
            update_player_stats(session.player_id, True, session.attempts)
            result['game_status'] = 'cleared'
            result['answer'] = target.name_ja
        else:
            # プレイヤーの最大試行回数を取得
            player_stats, _ = PlayerStats.objects.get_or_create(player_id=session.player_id)
            max_attempts = player_stats.max_attempts
            
            if session.attempts >= max_attempts:
                session.status = 'failed'
                session.save()
                update_player_stats(session.player_id, False, session.attempts)
                result['game_status'] = 'failed'
                result['answer'] = target.name_ja
            else:
                result['game_status'] = 'playing'
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def compare_types(guessed, target):
    """タイプの一致状況を判定"""
    guessed_types = {guessed.type1, guessed.type2} - {None}
    target_types = {target.type1, target.type2} - {None}
    
    if guessed_types == target_types:
        return 'match'
    elif guessed_types & target_types:  # 部分一致
        return 'partial'
    else:
        return 'mismatch'


def update_player_stats(player_id, cleared, attempts):
    """プレイヤー戦績を更新"""
    stats, created = PlayerStats.objects.get_or_create(player_id=player_id)
    
    stats.total_games += 1
    if cleared:
        stats.cleared_games += 1
        stats.total_attempts += attempts
        
        if stats.best_attempts is None or attempts < stats.best_attempts:
            stats.best_attempts = attempts
    
    stats.save()


def autocomplete(request):
    """オートコンプリート用のポケモン名リストを返す"""
    pokemon_list = Pokemon.objects.all().values_list('name_ja', flat=True)
    return JsonResponse({'pokemon': list(pokemon_list)})


def get_stats(request):
    """プレイヤー戦績を取得"""
    player_id = get_or_create_player_id(request)
    
    try:
        stats = PlayerStats.objects.get(player_id=player_id)
        return JsonResponse({
            'total_games': stats.total_games,
            'cleared_games': stats.cleared_games,
            'clear_rate': stats.clear_rate,
            'average_attempts': stats.average_attempts,
            'best_attempts': stats.best_attempts or 0,
        })
    except PlayerStats.DoesNotExist:
        return JsonResponse({
            'total_games': 0,
            'cleared_games': 0,
            'clear_rate': 0,
            'average_attempts': 0,
            'best_attempts': 0,
        })


def get_settings(request):
    """プレイヤー設定を取得"""
    player_id = get_or_create_player_id(request)
    
    try:
        stats = PlayerStats.objects.get(player_id=player_id)
        return JsonResponse({
            'max_attempts': stats.max_attempts,
        })
    except PlayerStats.DoesNotExist:
        return JsonResponse({
            'max_attempts': 8,  # デフォルト値
        })


@csrf_exempt
def update_settings(request):
    """プレイヤー設定を更新"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        max_attempts = data.get('max_attempts')
        
        if max_attempts is None:
            return JsonResponse({'error': 'max_attemptsが必要です'}, status=400)
        
        # バリデーション: 3～15の範囲
        try:
            max_attempts = int(max_attempts)
            if max_attempts < 3 or max_attempts > 15:
                return JsonResponse({'error': 'max_attemptsは3～15の範囲で指定してください'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'max_attemptsは数値で指定してください'}, status=400)
        
        # プレイヤーID取得
        player_id = get_or_create_player_id(request)
        
        # 設定を保存
        stats, created = PlayerStats.objects.get_or_create(player_id=player_id)
        stats.max_attempts = max_attempts
        stats.save()
        
        response = JsonResponse({
            'message': '設定を保存しました',
            'max_attempts': max_attempts,
        })
        
        # クッキーにプレイヤーIDを保存
        response.set_cookie('player_id', player_id, max_age=365*24*60*60)
        
        return response
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

