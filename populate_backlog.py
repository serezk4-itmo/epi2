"""Create detailed DPRO Scrum backlog. Uses YOUTRACK_TOKEN from the environment."""

import json
import os
import pathlib
import tomllib
import urllib.error
import urllib.parse
import urllib.request


PLAN = [
    (350, """pm|Согласовать роли пользователей и границы MVP
pm|Описать сценарии регистрации и публикации
be1|Подготовить доменную модель пользователей и публикаций
be2|Спроектировать API и карту интеграций
qa|Составить критерии приёмки и тестовую матрицу
devops|Описать требования к окружениям и безопасности"""),
    (350, """ux|Собрать карту пользовательских путей
ux|Подготовить прототип главной страницы и каталога
ux|Подготовить прототип профиля и проекта
fe1|Сверстать базовые элементы дизайн-системы
fe2|Настроить адаптивную сетку и типографику
qa|Проверить доступность и состояния интерфейса"""),
    (500, """devops|Подготовить контейнеры и конфигурацию окружений
be1|Реализовать регистрацию по email
be2|Реализовать вход и управление сессией
be1|Добавить восстановление доступа и подтверждение email
fe1|Собрать экраны входа и регистрации
fe2|Добавить маршруты и защиту клиентских разделов
qa|Покрыть авторизацию интеграционными тестами"""),
    (500, """be1|Сделать API профиля специалиста
be2|Сделать API студии и организации
fe1|Сверстать публичный профиль специалиста
fe2|Сверстать редактирование профиля
ux|Уточнить состояния пустого и заполненного профиля
qa|Проверить права доступа к профилям
devops|Настроить хранение аватаров и обложек"""),
    (550, """be1|Спроектировать модель проекта и категорий
be2|Реализовать создание и редактирование проекта
be1|Добавить черновики и публикацию
be2|Настроить загрузку изображений и медиа
fe1|Собрать форму редактора проекта
fe2|Сверстать публичную карточку проекта
qa|Проверить жизненный цикл публикации
devops|Настроить объектное хранилище медиа"""),
    (450, """be1|Добавить API фрагментов и ленты
be2|Реализовать реакции и подписки
fe1|Сверстать ленту фрагментов
fe2|Добавить кнопки реакций и подписки
qa|Проверить права на реакции и удаление
ux|Проверить мобильный сценарий ленты"""),
    (600, """be1|Настроить поисковый индекс проектов
be2|Добавить индекс специалистов и студий
be1|Реализовать фильтры и сортировку
be2|Добавить пагинацию и релевантность
fe1|Сверстать каталог проектов
fe2|Сверстать каталог специалистов
qa|Проверить поиск на пустых и больших выборках
devops|Настроить обновление поискового индекса"""),
    (450, """be1|Добавить очередь жалоб на публикации
be2|Реализовать действия модератора
fe1|Сверстать список жалоб
fe2|Сверстать панель управления категориями
qa|Проверить роли модератора и администратора
devops|Настроить журнал аудита действий"""),
    (550, """be1|Реализовать API вакансий
be2|Реализовать API заказов
be1|Добавить отклики и их статусы
fe1|Сверстать каталог вакансий
fe2|Сверстать форму публикации заказа
fe1|Сделать кабинет работодателя
qa|Проверить жизненный цикл вакансии
ux|Проверить сценарий отклика соискателя"""),
    (400, """be1|Реализовать модель школ и программ
be2|Добавить заявки на размещение
fe1|Сверстать каталог образования
fe2|Сверстать карточку школы и ментора
qa|Проверить фильтры образовательного каталога
ux|Проверить сценарий подачи заявки"""),
    (550, """pm|Согласовать состав тарифов PRO и ограничения
be1|Реализовать модель подписки и статусов
be2|Подключить тестовый платёжный сценарий
be1|Добавить обработку платежных ошибок
fe1|Сверстать страницу тарифов
fe2|Сверстать управление подпиской
qa|Проверить оплату и смену статуса
devops|Настроить секреты и журнал операций"""),
    (500, """be1|Реализовать события уведомлений
be2|Добавить настройки уведомлений пользователя
fe1|Сверстать центр уведомлений
fe2|Сверстать блок рекомендаций
qa|Проверить доставку и дубли уведомлений
pm|Согласовать правила базовых рекомендаций
devops|Настроить очередь фоновых событий"""),
    (600, """qa|Составить регрессионный набор сценариев
qa|Проверить авторизацию и профили end-to-end
qa|Проверить публикации и модерацию end-to-end
qa|Проверить поиск и отклики end-to-end
be1|Исправить выявленные ошибки API
fe1|Исправить выявленные ошибки интерфейса
devops|Провести нагрузочные прогоны
pm|Собрать реестр дефектов и приоритетов"""),
    (550, """be1|Закрыть критические дефекты backend
be2|Проверить права доступа и защиту API
fe1|Закрыть критические дефекты frontend
fe2|Проверить доступность и мобильную версию
qa|Повторно проверить исправленные дефекты
qa|Провести приёмочный регресс
devops|Проверить резервное копирование и восстановление
pm|Проверить готовность релизного объёма"""),
    (300, """devops|Подготовить production-конфигурацию
devops|Настроить CI для сборки и проверок
be1|Подготовить миграции базы данных
fe1|Проверить production-сборку интерфейса
qa|Подготовить релизный чек-лист
pm|Написать руководство администратора"""),
    (300, """pm|Провести приёмку пользовательских сценариев
qa|Проверить релизный чек-лист
devops|Выполнить релизную процедуру
be2|Проверить серверные логи после выпуска
fe2|Проверить публичные страницы после выпуска
pm|Зафиксировать итоги релиза и backlog улучшений"""),
]

CRITERIA = {
    "pm": "Результат согласован с командой, критерии проверяемы и записаны в проектной документации.",
    "ux": "Макет или схема покрывает основной и ошибочный сценарии, адаптивный вариант проверен.",
    "fe1": "Интерфейс соответствует макету, работает на мобильном экране и проходит ревью.",
    "fe2": "Интерфейс соответствует макету, работает на мобильном экране и проходит ревью.",
    "be1": "Контракт API описан, корректный и ошибочный сценарии покрыты тестами, код прошёл ревью.",
    "be2": "Контракт API описан, корректный и ошибочный сценарии покрыты тестами, код прошёл ревью.",
    "qa": "Результаты проверки и найденные дефекты зафиксированы в YouTrack; повторная проверка выполнена.",
    "devops": "Конфигурация хранится в репозитории без секретов, воспроизводится на тестовом окружении и задокументирована.",
}


def api(root, token, path, method="GET", body=None):
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
    request = urllib.request.Request(
        root + path,
        data=data,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method=method,
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main():
    config = tomllib.loads((pathlib.Path.home() / ".codex/config.toml").read_text())
    server = config["mcp_servers"]["youtrack"]
    parsed = urllib.parse.urlparse(server["url"])
    root = f"{parsed.scheme}://{parsed.netloc}"
    token = os.environ[server["bearer_token_env_var"]]
    existing = api(
        root,
        token,
        "/api/issues?query=project:%20DPRO&fields=idReadable,summary&$top=250",
    )
    existing_titles = {item["summary"] for item in existing}
    epic_ids = {}
    for item in existing:
        if item["idReadable"] in {f"DPRO-{n}" for n in range(1, 17)}:
            epic_ids[int(item["idReadable"].split("-")[1])] = item["idReadable"]
    assert len(epic_ids) == 16
    total = 0
    created = 0
    for sprint_no, (hours, task_text) in enumerate(PLAN, 1):
        tasks = [line.split("|", 1) for line in task_text.splitlines()]
        estimates = [hours // len(tasks) + (1 if i < hours % len(tasks) else 0) for i in range(len(tasks))]
        total += sum(estimates)
        sprint_name = api(
            root,
            token,
            f"/api/agiles/204-1/sprints?fields=id,name&$top=100",
        )[sprint_no]["name"]
        version = "0.1 Alpha" if sprint_no <= 4 else "0.5 Beta" if sprint_no <= 10 else "1.0 MVP"
        for (role, title), estimate in zip(tasks, estimates):
            if title in existing_titles:
                continue
            description = (
                f"Задача: {title}.\n\n"
                f"Критерии приёмки: {CRITERIA[role]} "
                "В описании PR указан ключ задачи; результат доступен для проверки."
            )
            body = {
                "project": {"id": "0-1"},
                "summary": title,
                "description": description,
                "customFields": [
                    {"name": "Type", "$type": "SingleEnumIssueCustomField", "value": {"name": "Task"}},
                    {"name": "Sprints", "$type": "MultiVersionIssueCustomField", "value": [{"name": sprint_name}]},
                    {"name": "Fix versions", "$type": "MultiVersionIssueCustomField", "value": [{"name": version}]},
                    {"name": "Assignee", "$type": "SingleUserIssueCustomField", "value": {"login": "dpro." + role}},
                    {"name": "DPRO Estimation", "$type": "PeriodIssueCustomField", "value": {"minutes": estimate * 60}},
                    {"name": "Original estimation", "$type": "SimpleIssueCustomField", "value": estimate},
                ],
            }
            issue = api(root, token, "/api/issues?fields=id,idReadable", "POST", body)
            api(
                root,
                token,
                f"/api/issues/{issue['idReadable']}/links/173-3t/issues?fields=idReadable",
                "POST",
                {"id": api(root, token, f"/api/issues/{epic_ids[sprint_no]}?fields=id")["id"]},
            )
            existing_titles.add(title)
            created += 1
        print(f"Sprint {sprint_no:02d}: {len(tasks)} tasks, {hours} h")
    assert total == 7500
    print("Created", created, "tasks; planned hours", total)


if __name__ == "__main__":
    main()
