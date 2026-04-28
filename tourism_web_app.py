"""
Локальный веб-интерфейс для рекомендательной системы туристических маршрутов.

Запуск:
    python tourism_web_app.py

После запуска откройте в браузере:
    http://127.0.0.1:8000

Веб-интерфейс использует только стандартную библиотеку Python и функции из
tourism_recommender.py, поэтому для дипломного проекта не нужны Flask/Django.
"""

from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs

from tourism_recommender import Recommendation, TouristRoute, UserProfile, build_route_database, recommend_routes


HOST = "127.0.0.1"
PORT = 8000

SEASON_OPTIONS = ["зима", "весна", "лето", "осень"]
ACTIVITY_OPTIONS = ["низкая", "средняя", "высокая"]


def escape(value: object) -> str:
    """Экранирует текст перед вставкой в HTML."""

    return html.escape(str(value), quote=True)


def route_options(routes: Sequence[TouristRoute]) -> Dict[str, List[str]]:
    """Формирует списки значений для выпадающих полей интерфейса."""

    return {
        "regions": sorted({route.region for route in routes}),
        "cities": sorted({route.city for route in routes}),
        "climates": sorted({route.climate for route in routes}),
        "interests": sorted(set().union(*(route.interests for route in routes))),
        "transports": sorted({route.transport for route in routes}),
    }


def option_tags(options: Sequence[str], selected: Optional[str], *, include_any: bool = True) -> str:
    """Создает HTML-теги option для select."""

    tags: List[str] = []
    if include_any:
        tags.append('<option value="">Любой вариант</option>')

    for option in options:
        is_selected = " selected" if option == selected else ""
        tags.append(f'<option value="{escape(option)}"{is_selected}>{escape(option)}</option>')
    return "\n".join(tags)


def multi_option_tags(options: Sequence[str], selected_values: Sequence[str]) -> str:
    """Создает option-теги для выбора нескольких интересов."""

    selected_set = set(selected_values)
    tags = []
    for option in options:
        is_selected = " selected" if option in selected_set else ""
        tags.append(f'<option value="{escape(option)}"{is_selected}>{escape(option)}</option>')
    return "\n".join(tags)


def default_form() -> Dict[str, object]:
    """Значения формы по умолчанию."""

    return {
        "region": "",
        "city": "",
        "season": "лето",
        "days": "3",
        "budget": "20000",
        "interests": [],
        "transport": "",
        "activity": "средняя",
        "climate": "",
        "accessible": "",
    }


def validate_form(data: Dict[str, object], routes: Sequence[TouristRoute]) -> Tuple[Optional[UserProfile], List[str]]:
    """Проверяет поля формы и создает профиль пользователя."""

    options = route_options(routes)
    errors: List[str] = []

    region = str(data.get("region", "")).strip()
    city = str(data.get("city", "")).strip()
    season = str(data.get("season", "")).strip()
    transport = str(data.get("transport", "")).strip()
    activity = str(data.get("activity", "")).strip()
    climate = str(data.get("climate", "")).strip()
    selected_interests = [str(item).strip() for item in data.get("interests", []) if str(item).strip()]

    if region and region not in options["regions"]:
        errors.append("Регион выбран некорректно.")
    if city and city not in options["cities"]:
        errors.append("Город выбран некорректно.")
    if season not in SEASON_OPTIONS:
        errors.append("Сезон выбран некорректно.")
    if transport and transport not in options["transports"]:
        errors.append("Транспорт выбран некорректно.")
    if activity not in ACTIVITY_OPTIONS:
        errors.append("Уровень активности выбран некорректно.")
    if climate and climate not in options["climates"]:
        errors.append("Климат выбран некорректно.")

    invalid_interests = sorted(set(selected_interests) - set(options["interests"]))
    if invalid_interests:
        errors.append("Некорректные интересы: " + ", ".join(invalid_interests))
    if len(selected_interests) > 5:
        errors.append("Выберите не более 5 интересов.")

    try:
        days = int(str(data.get("days", "")).strip())
        if not 1 <= days <= 14:
            errors.append("Количество дней должно быть от 1 до 14.")
    except ValueError:
        days = 3
        errors.append("Количество дней должно быть целым числом.")

    try:
        budget = int(str(data.get("budget", "")).strip())
        if not 3000 <= budget <= 200000:
            errors.append("Бюджет должен быть от 3000 до 200000 рублей.")
    except ValueError:
        budget = 20000
        errors.append("Бюджет должен быть целым числом.")

    if errors:
        return None, errors

    return UserProfile(
        preferred_city=city or None,
        preferred_region=region or None,
        season=season,
        days=days,
        max_budget=budget,
        interests=set(selected_interests),
        preferred_transport=transport or None,
        activity_level=activity,
        climate=climate or None,
        need_accessible_route=bool(data.get("accessible")),
    ), []


def recommendation_cards(recommendations: Sequence[Recommendation]) -> str:
    """Рендерит карточки маршрутов."""

    if not recommendations:
        return """
        <section class="empty-state">
            <h2>Маршруты не найдены</h2>
            <p>Попробуйте увеличить бюджет, выбрать другой сезон или убрать часть ограничений.</p>
        </section>
        """

    cards = []
    for item in recommendations:
        route = item.route
        reasons = "".join(f"<li>{escape(reason)}</li>" for reason in item.explanation)
        interests = ", ".join(sorted(route.interests)[:7])
        seasons = ", ".join(sorted(route.seasons))

        cards.append(
            f"""
            <article class="route-card">
                <div class="route-card__main">
                    <div>
                        <p class="route-card__eyebrow">{escape(route.region)} / {escape(route.city)}</p>
                        <h2>{escape(route.title)}</h2>
                    </div>
                    <strong class="score">{escape(item.score)}/100</strong>
                </div>
                <p class="description">{escape(route.description)}</p>
                <div class="facts">
                    <span>{escape(route.duration_days)} дн.</span>
                    <span>{escape(route.price)} руб.</span>
                    <span>{escape(route.transport)}</span>
                    <span>{escape(route.activity_level)} активность</span>
                </div>
                <dl class="details">
                    <div><dt>Сезоны</dt><dd>{escape(seasons)}</dd></div>
                    <div><dt>Интересы</dt><dd>{escape(interests)}</dd></div>
                </dl>
                <div class="reasons">
                    <h3>Почему подходит</h3>
                    <ul>{reasons}</ul>
                </div>
            </article>
            """
        )
    return "\n".join(cards)


def error_box(errors: Sequence[str]) -> str:
    """Рендерит блок ошибок формы."""

    if not errors:
        return ""
    items = "".join(f"<li>{escape(error)}</li>" for error in errors)
    return f'<div class="error-box"><strong>Проверьте поля формы</strong><ul>{items}</ul></div>'


def render_page(
    routes: Sequence[TouristRoute],
    form: Dict[str, object],
    recommendations: Sequence[Recommendation],
    errors: Sequence[str],
) -> str:
    """Собирает HTML-страницу."""

    options = route_options(routes)
    city_region_map = {route.city: route.region for route in routes}

    selected_interests = form.get("interests", [])
    if not isinstance(selected_interests, list):
        selected_interests = []

    accessible_checked = " checked" if form.get("accessible") else ""

    return f"""<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>TravelRoute - подбор маршрутов</title>
    <style>
        :root {{
            --text: #1f2933;
            --muted: #637083;
            --line: #d9e2ec;
            --panel: #ffffff;
            --page: #f4f7fb;
            --blue: #0065bd;
            --blue-dark: #034f8c;
            --green: #12805c;
            --yellow: #f7c948;
            --red: #c0342b;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            color: var(--text);
            background: var(--page);
        }}
        .topbar {{
            background: var(--panel);
            border-bottom: 1px solid var(--line);
        }}
        .topbar__inner {{
            max-width: 1180px;
            margin: 0 auto;
            padding: 18px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
        }}
        .brand {{
            font-size: 24px;
            font-weight: 700;
            color: var(--blue);
        }}
        .stats {{
            color: var(--muted);
            font-size: 14px;
        }}
        .hero {{
            background: linear-gradient(120deg, #dff2ff, #fff5cf);
            border-bottom: 1px solid var(--line);
        }}
        .hero__inner {{
            max-width: 1180px;
            margin: 0 auto;
            padding: 34px 24px 28px;
        }}
        .hero h1 {{
            margin: 0 0 10px;
            font-size: 34px;
            line-height: 1.15;
        }}
        .hero p {{
            margin: 0;
            max-width: 760px;
            color: var(--muted);
            font-size: 17px;
            line-height: 1.5;
        }}
        main {{
            max-width: 1180px;
            margin: 0 auto;
            padding: 24px;
            display: grid;
            grid-template-columns: 360px 1fr;
            gap: 24px;
            align-items: start;
        }}
        .search-panel, .route-card, .empty-state, .error-box {{
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
        }}
        .search-panel {{
            padding: 18px;
            position: sticky;
            top: 16px;
        }}
        .search-panel h2 {{
            margin: 0 0 16px;
            font-size: 20px;
        }}
        .form-grid {{
            display: grid;
            gap: 14px;
        }}
        label {{
            display: grid;
            gap: 6px;
            font-size: 14px;
            font-weight: 700;
        }}
        select, input[type="number"] {{
            width: 100%;
            min-height: 40px;
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: 8px 10px;
            font: inherit;
            background: #fff;
        }}
        select[multiple] {{
            min-height: 142px;
        }}
        .hint {{
            color: var(--muted);
            font-size: 12px;
            font-weight: 400;
        }}
        .checkbox {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
        }}
        .submit {{
            min-height: 44px;
            border: 0;
            border-radius: 6px;
            background: var(--blue);
            color: #fff;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
        }}
        .submit:hover {{ background: var(--blue-dark); }}
        .results {{
            display: grid;
            gap: 16px;
        }}
        .route-card {{
            padding: 20px;
        }}
        .route-card__main {{
            display: flex;
            justify-content: space-between;
            gap: 18px;
            align-items: start;
        }}
        .route-card__eyebrow {{
            margin: 0 0 6px;
            color: var(--green);
            font-size: 13px;
            font-weight: 700;
        }}
        .route-card h2 {{
            margin: 0;
            font-size: 22px;
            line-height: 1.25;
        }}
        .score {{
            flex: 0 0 auto;
            background: #e8f5ee;
            color: var(--green);
            border-radius: 6px;
            padding: 8px 10px;
        }}
        .description {{
            color: var(--muted);
            line-height: 1.45;
        }}
        .facts {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 14px 0;
        }}
        .facts span {{
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 6px 10px;
            background: #f8fafc;
            font-size: 13px;
        }}
        .details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin: 14px 0;
        }}
        .details div {{
            border-top: 1px solid var(--line);
            padding-top: 10px;
        }}
        dt {{
            color: var(--muted);
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        dd {{
            margin: 4px 0 0;
            line-height: 1.4;
        }}
        .reasons {{
            background: #fffbea;
            border-left: 4px solid var(--yellow);
            padding: 12px 14px;
            border-radius: 6px;
        }}
        .reasons h3 {{
            margin: 0 0 8px;
            font-size: 15px;
        }}
        .reasons ul, .error-box ul {{
            margin: 0;
            padding-left: 18px;
        }}
        .reasons li {{
            margin: 4px 0;
        }}
        .error-box {{
            padding: 14px 16px;
            border-color: #f2b8b5;
            color: var(--red);
            background: #fff4f2;
        }}
        .empty-state {{
            padding: 28px;
        }}
        @media (max-width: 860px) {{
            main {{
                grid-template-columns: 1fr;
            }}
            .search-panel {{
                position: static;
            }}
            .details {{
                grid-template-columns: 1fr;
            }}
            .hero h1 {{
                font-size: 28px;
            }}
        }}
    </style>
</head>
<body>
    <header class="topbar">
        <div class="topbar__inner">
            <div class="brand">TravelRoute</div>
            <div class="stats">{len(routes)} маршрутов / {len(options["cities"])} городов / {len(options["regions"])} регионов</div>
        </div>
    </header>

    <section class="hero">
        <div class="hero__inner">
            <h1>Подберите туристический маршрут</h1>
            <p>Выберите направление, сезон, бюджет и интересы. Система покажет подходящие маршруты и объяснит, почему они попали в выдачу.</p>
        </div>
    </section>

    <main>
        <aside class="search-panel">
            <h2>Параметры поездки</h2>
            <form class="form-grid" method="post" action="/recommend">
                <label>Регион
                    <select id="region" name="region">
                        {option_tags(options["regions"], str(form.get("region", "")))}
                    </select>
                </label>

                <label>Город
                    <select id="city" name="city">
                        {option_tags(options["cities"], str(form.get("city", "")))}
                    </select>
                </label>

                <label>Сезон
                    <select name="season">
                        {option_tags(SEASON_OPTIONS, str(form.get("season", "лето")), include_any=False)}
                    </select>
                </label>

                <label>Количество дней
                    <input name="days" type="number" min="1" max="14" value="{escape(form.get("days", "3"))}">
                </label>

                <label>Бюджет на человека, руб.
                    <input name="budget" type="number" min="3000" max="200000" step="500" value="{escape(form.get("budget", "20000"))}">
                </label>

                <label>Интересы
                    <select name="interests" multiple>
                        {multi_option_tags(options["interests"], selected_interests)}
                    </select>
                    <span class="hint">Можно выбрать до 5 вариантов. Если ничего не выбрать, интересы считаются любыми.</span>
                </label>

                <label>Транспорт
                    <select name="transport">
                        {option_tags(options["transports"], str(form.get("transport", "")))}
                    </select>
                </label>

                <label>Активность
                    <select name="activity">
                        {option_tags(ACTIVITY_OPTIONS, str(form.get("activity", "средняя")), include_any=False)}
                    </select>
                </label>

                <label>Климат
                    <select name="climate">
                        {option_tags(options["climates"], str(form.get("climate", "")))}
                    </select>
                </label>

                <label class="checkbox">
                    <input type="checkbox" name="accessible" value="1"{accessible_checked}>
                    Нужна доступная среда
                </label>

                <button class="submit" type="submit">Найти маршруты</button>
            </form>
        </aside>

        <section class="results">
            {error_box(errors)}
            {recommendation_cards(recommendations)}
        </section>
    </main>

    <script>
        const cityRegionMap = {json.dumps(city_region_map, ensure_ascii=False)};
        const regionSelect = document.querySelector("#region");
        const citySelect = document.querySelector("#city");

        function filterCities() {{
            const selectedRegion = regionSelect.value;
            for (const option of citySelect.options) {{
                if (!option.value) {{
                    option.hidden = false;
                    continue;
                }}
                option.hidden = Boolean(selectedRegion) && cityRegionMap[option.value] !== selectedRegion;
            }}
            const selectedCity = citySelect.value;
            if (selectedCity && cityRegionMap[selectedCity] !== selectedRegion && selectedRegion) {{
                citySelect.value = "";
            }}
        }}

        regionSelect.addEventListener("change", filterCities);
        filterCities();
    </script>
</body>
</html>"""


class TourismHandler(BaseHTTPRequestHandler):
    """HTTP-обработчик локального веб-приложения."""

    routes = build_route_database()

    def do_GET(self) -> None:
        if self.path not in {"/", "/recommend"}:
            self.send_error(404, "Страница не найдена")
            return
        recommendations = recommend_routes(self.routes, demo_web_profile(), top_n=8)
        self.respond(render_page(self.routes, default_form(), recommendations, []))

    def do_POST(self) -> None:
        if self.path != "/recommend":
            self.send_error(404, "Страница не найдена")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        parsed = parse_qs(body)

        form = default_form()
        for key in form:
            if key == "interests":
                form[key] = parsed.get(key, [])
            else:
                form[key] = parsed.get(key, [""])[0]

        profile, errors = validate_form(form, self.routes)
        recommendations = recommend_routes(self.routes, profile, top_n=10) if profile else []
        self.respond(render_page(self.routes, form, recommendations, errors))

    def respond(self, content: str) -> None:
        encoded = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        """Отключает шумный лог каждого запроса в консоли."""

        return


def demo_web_profile() -> UserProfile:
    """Профиль для первичной выдачи при открытии сайта."""

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


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), TourismHandler)
    print(f"TravelRoute запущен: http://{HOST}:{PORT}")
    print("Для остановки нажмите Ctrl+C.")
    server.serve_forever()


if __name__ == "__main__":
    main()
