from django.db import models
import uuid


class Pokemon(models.Model):
    """ポケモンの基本情報を格納するモデル"""
    pokedex_number = models.IntegerField(unique=True, verbose_name='図鑑番号')
    name_ja = models.CharField(max_length=100, verbose_name='日本語名')
    name_en = models.CharField(max_length=100, verbose_name='英語名')
    type1 = models.CharField(max_length=50, verbose_name='タイプ1')
    type2 = models.CharField(max_length=50, blank=True, null=True, verbose_name='タイプ2')
    height = models.FloatField(verbose_name='高さ(m)')
    weight = models.FloatField(verbose_name='重さ(kg)')
    generation = models.IntegerField(verbose_name='世代')
    evolution_count = models.IntegerField(default=0, verbose_name='進化回数')
    
    class Meta:
        verbose_name = 'ポケモン'
        verbose_name_plural = 'ポケモン'
        ordering = ['pokedex_number']
    
    def __str__(self):
        return f"No.{self.pokedex_number:04d} {self.name_ja}"


class GameSession(models.Model):
    """ゲームセッションを管理するモデル"""
    STATUS_CHOICES = [
        ('playing', 'プレイ中'),
        ('cleared', 'クリア'),
        ('failed', '失敗'),
    ]
    
    session_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    player_id = models.CharField(max_length=100, verbose_name='プレイヤーID')  # クッキーから取得
    target_pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE, verbose_name='お題ポケモン')
    attempts = models.IntegerField(default=0, verbose_name='試行回数')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='playing', verbose_name='状態')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        verbose_name = 'ゲームセッション'
        verbose_name_plural = 'ゲームセッション'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.player_id} - {self.target_pokemon.name_ja} ({self.status})"


class PlayerStats(models.Model):
    """プレイヤーの戦績を管理するモデル"""
    player_id = models.CharField(max_length=100, unique=True, verbose_name='プレイヤーID')
    total_games = models.IntegerField(default=0, verbose_name='総ゲーム数')
    cleared_games = models.IntegerField(default=0, verbose_name='クリア数')
    total_attempts = models.IntegerField(default=0, verbose_name='総試行回数')
    best_attempts = models.IntegerField(null=True, blank=True, verbose_name='最少試行回数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        verbose_name = 'プレイヤー戦績'
        verbose_name_plural = 'プレイヤー戦績'
    
    def __str__(self):
        return f"{self.player_id} - {self.cleared_games}/{self.total_games}"
    
    @property
    def clear_rate(self):
        """クリア率を計算"""
        if self.total_games == 0:
            return 0
        return round((self.cleared_games / self.total_games) * 100, 1)
    
    @property
    def average_attempts(self):
        """平均試行回数を計算"""
        if self.cleared_games == 0:
            return 0
        return round(self.total_attempts / self.cleared_games, 1)
