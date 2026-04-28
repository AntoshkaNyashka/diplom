"""
Дипломный пример: рекомендательная система для подбора туристических маршрутов.

Файл можно запускать напрямую:
    python tourism_recommender.py

Что реализовано:
1. Генерация большой базы маршрутов из CSV-файла с городами.
2. Профиль пользователя с условиями выбора: город, сезон, бюджет, дни,
   интересы, транспорт, уровень активности и требования доступности.
3. Гибридная рекомендательная логика:
   - жесткая фильтрация по обязательным ограничениям;
   - взвешенная оценка похожести маршрута на запрос;
   - объяснение, почему маршрут попал в рекомендации.

Код специально написан без внешних библиотек, чтобы его было проще
запустить на любом компьютере.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


BASE_DIR = Path(__file__).resolve().parent
CITY_CSV_PATH = BASE_DIR / "data" / "city.csv"


# -----------------------------
# Модели данных
# -----------------------------


@dataclass(frozen=True)
class CityProfile:
    """Описание туристического направления."""

    name: str
    region: str
    climate: str
    best_seasons: Set[str]
    base_cost_per_day: int
    popularity: int
    accessibility: int
    tags: Set[str]


@dataclass(frozen=True)
class RouteTemplate:
    """Шаблон маршрута, который комбинируется с городом."""

    name: str
    route_type: str
    interests: Set[str]
    min_days: int
    max_days: int
    activity_level: str
    transport: str
    cost_multiplier: float


@dataclass(frozen=True)
class TouristRoute:
    """Готовый туристический маршрут."""

    route_id: int
    title: str
    city: str
    region: str
    seasons: Set[str]
    duration_days: int
    price: int
    interests: Set[str]
    activity_level: str
    transport: str
    climate: str
    popularity: int
    accessibility: int
    description: str


@dataclass(frozen=True)
class UserProfile:
    """Профиль туриста, по которому строится рекомендация."""

    preferred_city: Optional[str]
    preferred_region: Optional[str]
    season: str
    days: int
    max_budget: int
    interests: Set[str]
    preferred_transport: Optional[str]
    activity_level: str
    climate: Optional[str]
    need_accessible_route: bool = False


@dataclass(frozen=True)
class Recommendation:
    """Результат работы рекомендательной системы."""

    route: TouristRoute
    score: float
    explanation: List[str]


# -----------------------------
# Справочники условий
# -----------------------------


SEASONS = {"зима", "весна", "лето", "осень", "круглый год"}

ACTIVITY_ORDER = {
    "низкая": 1,
    "средняя": 2,
    "высокая": 3,
}

TRANSPORT_COMPATIBILITY = {
    "пешком": {"пешком", "общественный транспорт"},
    "общественный транспорт": {"пешком", "общественный транспорт", "поезд"},
    "поезд": {"поезд", "общественный транспорт"},
    "авто": {"авто", "общественный транспорт"},
    "самолет": {"самолет", "общественный транспорт"},
    "велосипед": {"велосипед", "пешком"},
}


def build_fallback_city_profiles() -> List[CityProfile]:
    """Возвращает 40 направлений. Эти данные имитируют экспертную базу."""

    return [
        CityProfile("Москва", "Центральная Россия", "умеренный", {"весна", "лето", "осень", "зима"}, 6200, 10, 9, {"музеи", "театр", "архитектура", "гастрономия", "шопинг"}),
        CityProfile("Санкт-Петербург", "Северо-Запад", "прохладный", {"весна", "лето", "осень"}, 5900, 10, 8, {"музеи", "архитектура", "каналы", "театр", "история"}),
        CityProfile("Казань", "Поволжье", "умеренный", {"весна", "лето", "осень"}, 4300, 9, 8, {"история", "гастрономия", "архитектура", "религия", "набережные"}),
        CityProfile("Сочи", "Юг России", "субтропический", {"весна", "лето", "осень", "зима"}, 6500, 10, 7, {"море", "горы", "спорт", "природа", "гастрономия"}),
        CityProfile("Калининград", "Северо-Запад", "морской", {"весна", "лето", "осень"}, 5200, 8, 7, {"море", "архитектура", "история", "гастрономия", "замки"}),
        CityProfile("Владивосток", "Дальний Восток", "морской", {"лето", "осень"}, 6800, 8, 6, {"море", "мосты", "природа", "гастрономия", "острова"}),
        CityProfile("Иркутск", "Сибирь", "континентальный", {"лето", "зима"}, 5100, 8, 6, {"байкал", "природа", "история", "экскурсии", "зима"}),
        CityProfile("Екатеринбург", "Урал", "континентальный", {"весна", "лето", "осень"}, 4300, 7, 8, {"музеи", "архитектура", "индустриальный туризм", "история", "театр"}),
        CityProfile("Нижний Новгород", "Поволжье", "умеренный", {"весна", "лето", "осень"}, 4100, 8, 8, {"кремль", "реки", "история", "архитектура", "гастрономия"}),
        CityProfile("Ярославль", "Золотое кольцо", "умеренный", {"весна", "лето", "осень"}, 3500, 7, 8, {"история", "храмы", "архитектура", "музеи", "реки"}),
        CityProfile("Владимир", "Золотое кольцо", "умеренный", {"весна", "лето", "осень"}, 3300, 7, 8, {"история", "храмы", "архитектура", "музеи", "ремесла"}),
        CityProfile("Суздаль", "Золотое кольцо", "умеренный", {"весна", "лето", "осень", "зима"}, 3900, 8, 7, {"история", "храмы", "ремесла", "гастрономия", "фестивали"}),
        CityProfile("Псков", "Северо-Запад", "умеренный", {"весна", "лето", "осень"}, 3400, 6, 7, {"крепости", "история", "храмы", "природа", "музеи"}),
        CityProfile("Великий Новгород", "Северо-Запад", "умеренный", {"весна", "лето", "осень"}, 3600, 7, 8, {"кремль", "история", "храмы", "архитектура", "реки"}),
        CityProfile("Мурманск", "Север", "арктический", {"зима", "лето"}, 5400, 7, 6, {"северное сияние", "арктика", "море", "природа", "экскурсии"}),
        CityProfile("Петрозаводск", "Карелия", "прохладный", {"лето", "осень", "зима"}, 4200, 7, 6, {"озера", "лес", "природа", "этнография", "активный отдых"}),
        CityProfile("Горно-Алтайск", "Алтай", "горный", {"лето", "осень", "зима"}, 4800, 8, 5, {"горы", "природа", "треккинг", "этнография", "фото"}),
        CityProfile("Пятигорск", "Кавказ", "горный", {"весна", "лето", "осень"}, 4100, 7, 7, {"горы", "минеральные воды", "литература", "прогулки", "оздоровление"}),
        CityProfile("Кисловодск", "Кавказ", "горный", {"весна", "лето", "осень", "зима"}, 4700, 8, 8, {"оздоровление", "горы", "парки", "прогулки", "гастрономия"}),
        CityProfile("Дербент", "Кавказ", "теплый", {"весна", "лето", "осень"}, 3900, 7, 5, {"история", "крепости", "море", "гастрономия", "этнография"}),
        CityProfile("Махачкала", "Кавказ", "теплый", {"весна", "лето", "осень"}, 3800, 7, 5, {"море", "горы", "гастрономия", "этнография", "природа"}),
        CityProfile("Уфа", "Урал", "континентальный", {"весна", "лето", "осень", "зима"}, 3700, 6, 7, {"природа", "музеи", "национальная культура", "горы", "гастрономия"}),
        CityProfile("Пермь", "Урал", "континентальный", {"весна", "лето", "осень"}, 3600, 6, 7, {"театр", "музеи", "реки", "индустриальный туризм", "природа"}),
        CityProfile("Тюмень", "Сибирь", "континентальный", {"весна", "лето", "осень", "зима"}, 4200, 7, 8, {"термальные источники", "история", "гастрономия", "набережные", "оздоровление"}),
        CityProfile("Тобольск", "Сибирь", "континентальный", {"весна", "лето", "осень", "зима"}, 3500, 6, 6, {"кремль", "история", "музеи", "храмы", "сибирская культура"}),
        CityProfile("Красноярск", "Сибирь", "континентальный", {"лето", "осень", "зима"}, 4300, 7, 7, {"столбы", "природа", "реки", "спорт", "музеи"}),
        CityProfile("Новосибирск", "Сибирь", "континентальный", {"весна", "лето", "осень"}, 4000, 7, 8, {"театр", "наука", "музеи", "гастрономия", "городские прогулки"}),
        CityProfile("Томск", "Сибирь", "континентальный", {"весна", "лето", "осень"}, 3600, 6, 7, {"деревянная архитектура", "университеты", "музеи", "история", "кофейни"}),
        CityProfile("Омск", "Сибирь", "континентальный", {"весна", "лето", "осень"}, 3400, 5, 7, {"музеи", "история", "реки", "театр", "архитектура"}),
        CityProfile("Самара", "Поволжье", "умеренный", {"весна", "лето", "осень"}, 3900, 7, 8, {"волга", "набережные", "космос", "гастрономия", "архитектура"}),
        CityProfile("Саратов", "Поволжье", "умеренный", {"весна", "лето", "осень"}, 3300, 5, 7, {"волга", "музеи", "театр", "история", "набережные"}),
        CityProfile("Волгоград", "Юг России", "теплый", {"весна", "лето", "осень"}, 3700, 7, 7, {"история", "мемориалы", "волга", "музеи", "прогулки"}),
        CityProfile("Ростов-на-Дону", "Юг России", "теплый", {"весна", "лето", "осень"}, 4000, 7, 8, {"дон", "гастрономия", "история", "рынки", "архитектура"}),
        CityProfile("Астрахань", "Юг России", "сухой", {"весна", "лето", "осень"}, 3600, 6, 6, {"волга", "рыбалка", "кремль", "гастрономия", "природа"}),
        CityProfile("Кострома", "Золотое кольцо", "умеренный", {"весна", "лето", "осень", "зима"}, 3300, 6, 7, {"история", "храмы", "сыр", "ремесла", "волга"}),
        CityProfile("Рязань", "Центральная Россия", "умеренный", {"весна", "лето", "осень"}, 3200, 5, 7, {"кремль", "история", "литература", "музеи", "природа"}),
        CityProfile("Тула", "Центральная Россия", "умеренный", {"весна", "лето", "осень", "зима"}, 3400, 7, 8, {"музеи", "оружие", "пряники", "история", "гастрономия"}),
        CityProfile("Смоленск", "Центральная Россия", "умеренный", {"весна", "лето", "осень"}, 3200, 5, 6, {"крепости", "история", "музеи", "храмы", "природа"}),
        CityProfile("Выборг", "Северо-Запад", "прохладный", {"весна", "лето", "осень"}, 3900, 7, 6, {"замки", "парк", "архитектура", "история", "море"}),
        CityProfile("Йошкар-Ола", "Поволжье", "умеренный", {"весна", "лето", "осень"}, 3100, 5, 7, {"архитектура", "набережные", "национальная культура", "музеи", "гастрономия"}),
    ]


def parse_int(value: str, default: int = 0) -> int:
    """Безопасно переводит строку из CSV в число."""

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def parse_float(value: str, default: float = 0.0) -> float:
    """Безопасно переводит координаты из CSV в число."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: int, minimum: int, maximum: int) -> int:
    """Ограничивает число заданным диапазоном."""

    return max(minimum, min(maximum, value))


def format_region_name(region_type: str, region: str) -> str:
    """Преобразует сокращения из CSV в понятное название региона."""

    region_type = region_type.strip()
    region = region.strip()

    if not region:
        return "Регион не указан"

    prefixes = {
        "Респ": "Республика",
        "обл": "область",
        "край": "край",
        "АО": "автономный округ",
        "Аобл": "автономная область",
    }

    if region_type == "г":
        return region
    if region_type == "Чувашия":
        return "Чувашская Республика"
    if region_type == "Респ":
        return f"Республика {region}"
    if region_type in prefixes:
        return f"{region} {prefixes[region_type]}"
    return f"{region_type} {region}".strip()


def infer_climate(row: Dict[str, str]) -> str:
    """Грубо определяет климат по координатам и федеральному округу."""

    latitude = parse_float(row.get("geo_lat", "0"))
    district = row.get("federal_district", "")
    region = row.get("region", "")

    if latitude >= 66:
        return "арктический"
    if district == "Северо-Кавказский" or region in {"Алтай", "Дагестан", "Кабардино-Балкария", "Карачаево-Черкесия"}:
        return "горный"
    if district == "Южный" and latitude < 48:
        return "теплый"
    if district in {"Дальневосточный", "Северо-Западный"} and latitude < 60:
        return "прохладный"
    if latitude >= 58:
        return "прохладный"
    return "континентальный"


def seasons_for_climate(climate: str) -> Set[str]:
    """Определяет лучшие сезоны поездки по климату."""

    if climate == "арктический":
        return {"лето", "зима"}
    if climate == "горный":
        return {"весна", "лето", "осень", "зима"}
    if climate == "теплый":
        return {"весна", "лето", "осень"}
    if climate == "прохладный":
        return {"лето", "осень", "зима"}
    return {"весна", "лето", "осень"}


def tags_for_city(row: Dict[str, str], population: int) -> Set[str]:
    """Формирует туристические интересы для города из признаков CSV."""

    city = row.get("city", "")
    region = row.get("region", "")
    district = row.get("federal_district", "")
    tags = {"история", "архитектура", "музеи", "городские прогулки"}

    if population >= 300_000:
        tags |= {"театр", "гастрономия", "набережные"}
    if population >= 1_000_000:
        tags |= {"шопинг", "выставки", "событийный туризм"}

    district_tags = {
        "Центральный": {"история", "усадьбы", "музеи"},
        "Северо-Западный": {"крепости", "озера", "природа"},
        "Южный": {"гастрономия", "теплый климат", "реки"},
        "Северо-Кавказский": {"горы", "оздоровление", "этнография"},
        "Приволжский": {"волга", "национальная культура", "набережные"},
        "Уральский": {"горы", "индустриальный туризм", "природа"},
        "Сибирский": {"природа", "реки", "сибирская культура"},
        "Дальневосточный": {"природа", "море", "экспедиции"},
    }
    tags |= district_tags.get(district, set())

    keywords = f"{city} {region}".lower()
    if any(word in keywords for word in ["сочи", "анапа", "геленджик", "евпатория", "ялта", "севастополь"]):
        tags |= {"море", "пляж", "курорт"}
    if any(word in keywords for word in ["алтай", "кавказ", "эльбрус", "пятигорск", "кисловодск"]):
        tags |= {"горы", "треккинг", "фото"}
    if any(word in keywords for word in ["байкал", "иркутск", "улан-удэ"]):
        tags |= {"байкал", "озера", "природа"}
    if any(word in keywords for word in ["казань", "уфа", "йошкар", "чебоксары", "дербент"]):
        tags |= {"национальная культура", "гастрономия"}
    if any(word in keywords for word in ["новгород", "псков", "смоленск", "выборг"]):
        tags |= {"крепости", "храмы"}

    return tags


def score_by_population(population: int, capital_marker: int) -> int:
    """Оценивает туристическую заметность города по населению и статусу."""

    if population >= 3_000_000:
        score = 10
    elif population >= 1_000_000:
        score = 9
    elif population >= 500_000:
        score = 8
    elif population >= 250_000:
        score = 7
    elif population >= 100_000:
        score = 6
    elif population >= 50_000:
        score = 5
    else:
        score = 4

    if capital_marker >= 2:
        score += 1
    return clamp(score, 1, 10)


def build_city_profiles_from_csv(csv_path: Path = CITY_CSV_PATH) -> List[CityProfile]:
    """Создает профили городов из приложенного CSV-файла."""

    if not csv_path.exists():
        return []

    with csv_path.open("r", encoding="utf-8", newline="") as file:
        rows = [row for row in csv.DictReader(file) if row.get("city")]

    city_name_counts: Dict[str, int] = {}
    for row in rows:
        city = row.get("city", "").strip()
        city_name_counts[city] = city_name_counts.get(city, 0) + 1

    profiles: List[CityProfile] = []

    for row in rows:
        city = row.get("city", "").strip()
        region = format_region_name(row.get("region_type", ""), row.get("region", ""))
        population = parse_int(row.get("population", "0"))
        capital_marker = parse_int(row.get("capital_marker", "0"))
        popularity = score_by_population(population, capital_marker)
        climate = infer_climate(row)

        # Если название города повторяется в разных регионах, добавляем регион
        # прямо в отображаемое имя, чтобы выбор в интерфейсе был однозначным.
        display_city = city if city_name_counts.get(city, 0) == 1 else f"{city} ({region})"

        base_cost = 2600 + popularity * 260
        if capital_marker >= 2:
            base_cost += 500
        if row.get("federal_district") in {"Дальневосточный", "Северо-Западный"}:
            base_cost += 350

        profiles.append(
            CityProfile(
                name=display_city,
                region=region,
                climate=climate,
                best_seasons=seasons_for_climate(climate),
                base_cost_per_day=clamp(base_cost, 2800, 7600),
                popularity=popularity,
                accessibility=clamp(popularity + (1 if capital_marker >= 2 else 0), 4, 10),
                tags=tags_for_city(row, population),
            )
        )

    return profiles


def build_city_profiles() -> List[CityProfile]:
    """
    Возвращает базу городов.

    Основной источник - data/city.csv. Если файла нет, используется маленькая
    встроенная база, чтобы программа все равно запускалась.
    """

    csv_profiles = build_city_profiles_from_csv()
    return csv_profiles or build_fallback_city_profiles()


def build_route_templates() -> List[RouteTemplate]:
    """Шесть типов маршрутов для каждого города."""

    return [
        RouteTemplate("Классический уикенд", "обзорный", {"история", "архитектура", "музеи", "прогулки"}, 2, 3, "низкая", "общественный транспорт", 1.00),
        RouteTemplate("Гастрономическое путешествие", "гастрономический", {"гастрономия", "рынки", "кофейни", "национальная культура"}, 2, 4, "низкая", "пешком", 1.18),
        RouteTemplate("Активный маршрут", "активный", {"природа", "спорт", "треккинг", "горы", "велосипед"}, 3, 6, "высокая", "авто", 1.25),
        RouteTemplate("Культурная программа", "культурный", {"музеи", "театр", "история", "литература", "экскурсии"}, 3, 5, "средняя", "общественный транспорт", 1.12),
        RouteTemplate("Семейный отдых", "семейный", {"парки", "музеи", "природа", "прогулки", "оздоровление"}, 4, 7, "низкая", "авто", 1.15),
        RouteTemplate("Фототур и необычные места", "фототур", {"фото", "архитектура", "природа", "море", "набережные"}, 2, 5, "средняя", "пешком", 1.08),
    ]


def build_route_database() -> List[TouristRoute]:
    """Создает маршруты на основе городов и шаблонов."""

    routes: List[TouristRoute] = []
    route_id = 1

    for city in build_city_profiles():
        for template in build_route_templates():
            # Длительность маршрута зависит от популярности направления:
            # для более популярных городов программа чуть насыщеннее.
            duration = min(
                template.max_days,
                template.min_days + (1 if city.popularity >= 8 else 0),
            )

            # Цена считается как базовая стоимость города * дни * коэффициент
            # маршрута. Округляем до сотен, чтобы выглядело как реальный тур.
            raw_price = city.base_cost_per_day * duration * template.cost_multiplier
            price = int(round(raw_price / 100) * 100)

            interests = set(city.tags) | set(template.interests)

            routes.append(
                TouristRoute(
                    route_id=route_id,
                    title=f"{city.name}: {template.name}",
                    city=city.name,
                    region=city.region,
                    seasons=set(city.best_seasons),
                    duration_days=duration,
                    price=price,
                    interests=interests,
                    activity_level=template.activity_level,
                    transport=template.transport,
                    climate=city.climate,
                    popularity=city.popularity,
                    accessibility=city.accessibility,
                    description=(
                        f"{template.route_type.capitalize()} маршрут по направлению "
                        f"{city.name}: основные точки интереса, локальная культура "
                        f"и удобная логистика для туриста."
                    ),
                )
            )
            route_id += 1

    if not routes:
        raise RuntimeError("База маршрутов не создана: нет городов или шаблонов.")
    return routes


# -----------------------------
# Алгоритм рекомендации
# -----------------------------


def normalize(value: float, min_value: float, max_value: float) -> float:
    """Переводит значение к диапазону 0..1."""

    if max_value == min_value:
        return 1.0
    return max(0.0, min(1.0, (value - min_value) / (max_value - min_value)))


def jaccard_similarity(left: Set[str], right: Set[str]) -> float:
    """Считает сходство двух наборов интересов."""

    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def season_score(route: TouristRoute, requested_season: str) -> float:
    """Оценивает соответствие маршрута сезону поездки."""

    if requested_season in route.seasons:
        return 1.0
    if "круглый год" in route.seasons:
        return 0.9
    return 0.15


def duration_score(route: TouristRoute, requested_days: int) -> float:
    """Чем ближе длительность маршрута к желаемой, тем выше оценка."""

    difference = abs(route.duration_days - requested_days)
    if difference == 0:
        return 1.0
    if difference == 1:
        return 0.75
    if difference == 2:
        return 0.45
    return 0.15


def budget_score(route: TouristRoute, max_budget: int) -> float:
    """Оценивает маршрут по бюджету: дешевле лимита — лучше."""

    if route.price <= max_budget:
        reserve = max_budget - route.price
        return 0.75 + 0.25 * normalize(reserve, 0, max_budget)

    # Если маршрут дороже, он не отбрасывается сразу: иногда пользователь
    # может захотеть увидеть близкий вариант, но штраф будет существенным.
    overrun = route.price - max_budget
    return max(0.0, 0.65 - normalize(overrun, 0, max_budget) * 0.65)


def activity_score(route: TouristRoute, requested_activity: str) -> float:
    """Сравнивает желаемую и фактическую физическую нагрузку."""

    route_level = ACTIVITY_ORDER[route.activity_level]
    requested_level = ACTIVITY_ORDER[requested_activity]
    difference = abs(route_level - requested_level)
    if difference == 0:
        return 1.0
    if difference == 1:
        return 0.65
    return 0.25


def transport_score(route: TouristRoute, preferred_transport: Optional[str]) -> float:
    """Проверяет совместимость транспорта."""

    if preferred_transport is None:
        return 0.8
    if route.transport == preferred_transport:
        return 1.0
    compatible = TRANSPORT_COMPATIBILITY.get(preferred_transport, {preferred_transport})
    return 0.65 if route.transport in compatible else 0.25


def location_score(route: TouristRoute, profile: UserProfile) -> float:
    """Учитывает желаемый город или регион."""

    if profile.preferred_city and route.city.lower() == profile.preferred_city.lower():
        return 1.0
    if profile.preferred_region and route.region.lower() == profile.preferred_region.lower():
        return 0.8
    if not profile.preferred_city and not profile.preferred_region:
        return 0.6
    return 0.25


def climate_score(route: TouristRoute, preferred_climate: Optional[str]) -> float:
    """Оценивает климатическое предпочтение пользователя."""

    if preferred_climate is None:
        return 0.7
    return 1.0 if route.climate == preferred_climate else 0.35


def accessibility_score(route: TouristRoute, need_accessible_route: bool) -> float:
    """Учитывает доступность маршрута для маломобильных туристов."""

    if not need_accessible_route:
        return normalize(route.accessibility, 1, 10)
    return 1.0 if route.accessibility >= 8 else normalize(route.accessibility, 1, 10) * 0.55


def build_explanation(route: TouristRoute, profile: UserProfile, parts: Dict[str, float]) -> List[str]:
    """Формирует человеко-понятное объяснение рекомендации."""

    explanation: List[str] = []

    if parts["season"] >= 0.9:
        explanation.append(f"подходит для сезона: {profile.season}")
    if parts["budget"] >= 0.75:
        explanation.append(f"укладывается в бюджет: {route.price} руб. <= {profile.max_budget} руб.")
    if parts["interests"] > 0:
        matched = sorted(route.interests & profile.interests)
        explanation.append("совпадающие интересы: " + ", ".join(matched[:5]))
    if parts["duration"] >= 0.75:
        explanation.append(f"длительность близка к запросу: {route.duration_days} дн.")
    if parts["location"] >= 0.8:
        explanation.append(f"совпадает направление: {route.city}, {route.region}")
    if parts["transport"] >= 0.65:
        explanation.append(f"подходящий транспорт: {route.transport}")
    if profile.need_accessible_route and route.accessibility >= 8:
        explanation.append("маршрут имеет высокий показатель доступности")

    return explanation or ["маршрут получил высокую суммарную оценку по нескольким параметрам"]


def score_route(route: TouristRoute, profile: UserProfile) -> Recommendation:
    """
    Считает итоговую оценку маршрута.

    Весовые коэффициенты можно описать в дипломе как экспертную модель:
    чем важнее параметр для туриста, тем больше его вклад в итоговую оценку.
    """

    parts = {
        "location": location_score(route, profile),
        "season": season_score(route, profile.season),
        "budget": budget_score(route, profile.max_budget),
        "duration": duration_score(route, profile.days),
        "interests": 0.55 if not profile.interests else jaccard_similarity(route.interests, profile.interests),
        "activity": activity_score(route, profile.activity_level),
        "transport": transport_score(route, profile.preferred_transport),
        "climate": climate_score(route, profile.climate),
        "accessibility": accessibility_score(route, profile.need_accessible_route),
        "popularity": normalize(route.popularity, 1, 10),
    }

    weights = {
        "location": 0.14,
        "season": 0.13,
        "budget": 0.16,
        "duration": 0.11,
        "interests": 0.20,
        "activity": 0.08,
        "transport": 0.06,
        "climate": 0.04,
        "accessibility": 0.04,
        "popularity": 0.04,
    }

    total_score = sum(parts[name] * weights[name] for name in weights)
    explanation = build_explanation(route, profile, parts)
    return Recommendation(route=route, score=round(total_score * 100, 2), explanation=explanation)


def passes_hard_filters(route: TouristRoute, profile: UserProfile) -> bool:
    """
    Жесткие ограничения.

    Они нужны, чтобы явно неподходящие маршруты не попадали в выдачу:
    например, недоступный маршрут при обязательном требовании доступности.
    """

    if profile.need_accessible_route and route.accessibility < 6:
        return False

    if profile.season not in SEASONS:
        raise ValueError(f"Неизвестный сезон: {profile.season}")

    if profile.activity_level not in ACTIVITY_ORDER:
        raise ValueError(f"Неизвестный уровень активности: {profile.activity_level}")

    # Оставляем небольшой запас выше бюджета, чтобы показать близкие варианты.
    if route.price > profile.max_budget * 1.25:
        return False

    # Слишком длинный или слишком короткий маршрут будет неудобен.
    if abs(route.duration_days - profile.days) > 3:
        return False

    return True


def recommend_routes(
    routes: Sequence[TouristRoute],
    profile: UserProfile,
    top_n: int = 10,
) -> List[Recommendation]:
    """Возвращает top_n лучших маршрутов для пользователя."""

    candidates = [route for route in routes if passes_hard_filters(route, profile)]
    scored = [score_route(route, profile) for route in candidates]
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_n]


# -----------------------------
# Вспомогательные функции вывода
# -----------------------------


def print_available_conditions(routes: Sequence[TouristRoute]) -> None:
    """Показывает размер базы и доступные условия выбора."""

    cities = sorted({route.city for route in routes})
    regions = sorted({route.region for route in routes})
    climates = sorted({route.climate for route in routes})
    interests = sorted(set().union(*(route.interests for route in routes)))

    print("База маршрутов")
    print("-" * 60)
    print(f"Количество маршрутов: {len(routes)}")
    print(f"Количество городов/направлений: {len(cities)}")
    print(f"Количество регионов: {len(regions)}")
    print(f"Количество интересов: {len(interests)}")
    print(f"Сезоны: {', '.join(sorted(SEASONS))}")
    print(f"Климаты: {', '.join(climates)}")
    print()


def print_recommendations(recommendations: Iterable[Recommendation]) -> None:
    """Красиво печатает список рекомендаций."""

    recommendations = list(recommendations)

    print("Рекомендованные маршруты")
    print("-" * 60)

    if not recommendations:
        print("По заданным условиям маршруты не найдены. Попробуйте увеличить бюджет или количество дней.")
        return

    for index, recommendation in enumerate(recommendations, start=1):
        route = recommendation.route
        print(f"{index}. {route.title}")
        print(f"   Оценка: {recommendation.score}/100")
        print(f"   Город/регион: {route.city}, {route.region}")
        print(f"   Сезоны: {', '.join(sorted(route.seasons))}")
        print(f"   Длительность: {route.duration_days} дн.")
        print(f"   Стоимость: {route.price} руб.")
        print(f"   Активность: {route.activity_level}")
        print(f"   Транспорт: {route.transport}")
        print(f"   Интересы: {', '.join(sorted(route.interests)[:8])}")
        print("   Почему подходит:")
        for reason in recommendation.explanation:
            print(f"   - {reason}")
        print()


def demo_profile() -> UserProfile:
    """Пример анкеты туриста для демонстрации работы системы."""

    return UserProfile(
        preferred_city=None,
        preferred_region="Ставропольский край",
        season="лето",
        days=4,
        max_budget=23000,
        interests={"горы", "природа", "гастрономия", "история"},
        preferred_transport="авто",
        activity_level="средняя",
        climate="горный",
        need_accessible_route=False,
    )


def print_search_header() -> None:
    """Печатает заголовок анкеты в стиле туристического сервиса."""

    print()
    print("=" * 72)
    print("                 TravelRoute - подбор туристического маршрута")
    print("=" * 72)
    print("Заполните параметры поездки. Можно выбрать номер варианта или ввести название.")
    print("Если параметр не важен, выберите 0 - любой вариант.")
    print()


def get_route_options(routes: Sequence[TouristRoute]) -> Dict[str, List[str]]:
    """Собирает справочники, из которых пользователь выбирает значения."""

    return {
        "regions": sorted({route.region for route in routes}),
        "cities": sorted({route.city for route in routes}),
        "climates": sorted({route.climate for route in routes}),
        "interests": sorted(set().union(*(route.interests for route in routes))),
        "transports": sorted({route.transport for route in routes}),
    }


def print_numbered_options(options: Sequence[str], columns: int = 2) -> None:
    """Выводит варианты в несколько колонок, чтобы список был похож на каталог."""

    if not options:
        return

    width = max(len(option) for option in options) + 8
    for index, option in enumerate(options, start=1):
        text = f"{index:>2}. {option}"
        print(text.ljust(width), end="")
        if index % columns == 0:
            print()
    if len(options) % columns != 0:
        print()


def ask_choice(
    title: str,
    options: Sequence[str],
    *,
    allow_any: bool = True,
    default: Optional[str] = None,
) -> Optional[str]:
    """
    Просит выбрать один вариант.

    Пользователь может ввести номер из списка или само название. Ошибка ввода
    не завершает программу, а возвращает к этому же вопросу.
    """

    normalized_options = {option.lower(): option for option in options}

    while True:
        print(title)
        print("-" * 72)
        if allow_any:
            print(" 0. любой вариант")
        print_numbered_options(options)

        default_hint = f" [{default}]" if default else ""
        raw_value = input(f"Ваш выбор{default_hint}: ").strip()
        print()

        if not raw_value and default is not None:
            return default
        if allow_any and raw_value in {"", "0", "любой", "любая", "все"}:
            return None
        if raw_value.isdigit():
            number = int(raw_value)
            if 1 <= number <= len(options):
                return options[number - 1]

        selected = normalized_options.get(raw_value.lower())
        if selected:
            return selected

        print("Ошибка: такого варианта нет в списке. Введите номер или точное название.")
        print()


def ask_multi_choice(title: str, options: Sequence[str], *, max_items: int = 5) -> Set[str]:
    """
    Просит выбрать несколько интересов.

    Поддерживает ввод номеров и названий через запятую: например, "1, 4, музеи".
    """

    normalized_options = {option.lower(): option for option in options}

    while True:
        print(title)
        print("-" * 72)
        print(" 0. любые интересы")
        print_numbered_options(options, columns=3)

        raw_value = input(f"Выберите до {max_items} вариантов через запятую: ").strip()
        print()

        if raw_value in {"", "0", "любой", "любые", "все"}:
            return set()

        selected: Set[str] = set()
        invalid_values: List[str] = []

        for item in raw_value.split(","):
            value = item.strip()
            if not value:
                continue
            if value.isdigit():
                number = int(value)
                if 1 <= number <= len(options):
                    selected.add(options[number - 1])
                else:
                    invalid_values.append(value)
                continue

            option = normalized_options.get(value.lower())
            if option:
                selected.add(option)
            else:
                invalid_values.append(value)

        if invalid_values:
            print("Ошибка: не найдены варианты: " + ", ".join(invalid_values))
            print("Введите номера из списка или точные названия интересов.")
            print()
            continue

        if len(selected) > max_items:
            print(f"Ошибка: выбрано слишком много интересов. Максимум: {max_items}.")
            print()
            continue

        if selected:
            return selected

        print("Ошибка: не удалось распознать выбор. Попробуйте еще раз.")
        print()


def ask_int(title: str, *, default: int, min_value: int, max_value: int) -> int:
    """Просит ввести целое число в заданном диапазоне."""

    while True:
        raw_value = input(f"{title} [{default}]: ").strip()
        if not raw_value:
            return default

        try:
            value = int(raw_value)
        except ValueError:
            print("Ошибка: нужно ввести целое число.")
            continue

        if min_value <= value <= max_value:
            return value

        print(f"Ошибка: значение должно быть от {min_value} до {max_value}.")


def ask_yes_no(title: str, *, default: bool = False) -> bool:
    """Просит ответить да или нет."""

    default_text = "да" if default else "нет"
    positive = {"да", "д", "yes", "y", "1"}
    negative = {"нет", "н", "no", "n", "0"}

    while True:
        raw_value = input(f"{title} (да/нет) [{default_text}]: ").strip().lower()
        if not raw_value:
            return default
        if raw_value in positive:
            return True
        if raw_value in negative:
            return False
        print("Ошибка: введите 'да' или 'нет'.")


def interactive_profile(routes: Sequence[TouristRoute]) -> UserProfile:
    """
    Консольный интерфейс выбора маршрута.

    Он имитирует форму туристического сайта: пользователь видит доступные
    направления, выбирает значения из справочников и не перезапускает программу
    при ошибке ввода.
    """

    options = get_route_options(routes)
    print_search_header()

    preferred_region = ask_choice("Куда поедем: выберите регион", options["regions"])

    city_options = options["cities"]
    if preferred_region:
        city_options = sorted({route.city for route in routes if route.region == preferred_region})

    preferred_city = ask_choice("Выберите город или направление", city_options)
    season = ask_choice("Когда планируется поездка", ["зима", "весна", "лето", "осень"], allow_any=False, default="лето")
    days = ask_int("Количество дней поездки", default=3, min_value=1, max_value=14)
    max_budget = ask_int("Максимальный бюджет на человека, руб.", default=20000, min_value=3000, max_value=200000)
    interests = ask_multi_choice("Что интересно в поездке", options["interests"])
    preferred_transport = ask_choice("Предпочтительный транспорт", options["transports"])
    activity_level = ask_choice("Комфортный уровень активности", ["низкая", "средняя", "высокая"], allow_any=False, default="средняя")
    climate = ask_choice("Желаемый климат", options["climates"])
    need_accessible_route = ask_yes_no("Нужна доступная среда", default=False)

    return UserProfile(
        preferred_city=preferred_city,
        preferred_region=preferred_region,
        season=season,
        days=days,
        max_budget=max_budget,
        interests=interests,
        preferred_transport=preferred_transport,
        activity_level=activity_level,
        climate=climate,
        need_accessible_route=need_accessible_route,
    )


def ask_start_mode() -> str:
    """Выбор режима запуска с проверкой ошибки."""

    while True:
        print("Режимы запуска:")
        print("1 - демо-профиль")
        print("2 - подобрать маршрут через форму выбора")
        mode = input("Выберите режим (1/2): ").strip() or "1"
        if mode in {"1", "2"}:
            return mode
        print("Ошибка: выберите 1 или 2.")
        print()


def main() -> None:
    routes = build_route_database()
    print_available_conditions(routes)

    mode = ask_start_mode()

    profile = interactive_profile(routes) if mode == "2" else demo_profile()
    recommendations = recommend_routes(routes, profile, top_n=10)

    print()
    print_recommendations(recommendations)


if __name__ == "__main__":
    main()
