from django.core.management.base import BaseCommand
from game.pokeapi_service import fetch_pokemon_data
from game.models import Pokemon
import time


class Command(BaseCommand):
    help = 'PokeAPIからポケモンデータを取得してデータベースに保存します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=151,
            help='取得するポケモンの数（デフォルト: 151 - 第1世代）'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write(self.style.SUCCESS(f'PokeAPIから{limit}匹のポケモンデータを取得します...'))
        
        success_count = 0
        error_count = 0
        
        for i in range(1, limit + 1):
            try:
                self.stdout.write(f'ポケモン #{i} を取得中...')
                
                pokemon_data = fetch_pokemon_data(i)
                
                if pokemon_data:
                    # 既存のポケモンを更新または新規作成
                    pokemon, created = Pokemon.objects.update_or_create(
                        pokedex_number=pokemon_data['pokedex_number'],
                        defaults=pokemon_data
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'  ✓ {pokemon.name_ja} を作成しました'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'  ✓ {pokemon.name_ja} を更新しました'))
                    
                    success_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f'  ✗ ポケモン #{i} のデータ取得に失敗しました'))
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ エラー: {str(e)}'))
                error_count += 1
            
            # API負荷軽減のため少し待機
            time.sleep(0.5)
        
        self.stdout.write(self.style.SUCCESS(f'\n完了: {success_count}匹成功, {error_count}匹失敗'))
