# Lab 8 — GraphQL alongside REST

Каталог курсов на FastAPI, SQLAlchemy, PostgreSQL и Strawberry. REST и GraphQL используют одну базу и общий `services.py`. Фронтенд на Next.js показывает учебный план студента двумя способами.

## 1. Запуск с нуля

Проверено 12.11.2026 на Windows: Python 3.12, PostgreSQL 17.4, SQLAlchemy 2.1.8, Strawberry 0.341.2, FastAPI 0.162.5. Для фронтенда — Node.js 24.21, Next.js 16.4.6 и React 19.3.1.

Учебный PostgreSQL работает на **127.0.0.1:55432**. Для Lab 8 используется отдельная база **course_catalog_lab8**. База седьмой работы `course_catalog` сохраняется.

```powershell
pg_isready -h 127.0.0.1 -p 55432
psql -h 127.0.0.1 -p 55432 -U postgres -d postgres
```

В psql создайте отсутствующие роль и базу. Если роль уже есть после прошлых лабораторных, повторять CREATE ROLE не нужно.

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog_lab8 OWNER catalog_app;
\q
```

Из папки `course-catalog-api`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe check_db.py
.\.venv\Scripts\python.exe -m alembic upgrade head
psql -h 127.0.0.1 -p 55432 -U catalog_app -d course_catalog_lab8 -v ON_ERROR_STOP=1 -f seed.sql
.\.venv\Scripts\python.exe check_models.py
.\.venv\Scripts\python.exe -m alembic check
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

`seed.sql` сбрасывает только данные выбранной базы и возвращает 6 курсов, 3 студентов, 6 записей. Используйте его для учебных экспериментов. При обычном повторном запуске достаточно последней команды. Для просмотра SQL задайте `SQL_ECHO=true` в `.env` и перезапустите API.

[REST / Swagger](http://127.0.0.1:8000/docs) · [GraphiQL](http://127.0.0.1:8000/graphql).

В другом терминале, из той же папки:

```powershell
.\.venv\Scripts\python.exe try_errors.py
.\.venv\Scripts\python.exe try_graphql.py
.\.venv\Scripts\python.exe try_n_plus_1.py
.\.venv\Scripts\python.exe try_protection.py
.\.venv\Scripts\python.exe flood_likes.py
.\.venv\Scripts\python.exe measure.py
.\.venv\Scripts\python.exe print_schema.py
```

Ожидается 5/5 REST, 8/8 GraphQL, SQL 3/3, защита 6/6, отклонение 12 мутаций до SQL. Скрипты возвращают ненулевой код при несоответствии проверяемого контракта; `try_n_plus_1.py` выводит измеренные числа. `measure.py` также сравнивает данные обоих экранов.

Фронтенд находится в соседней папке `course-catalog`. Он создан заново для этой лабораторной по согласованию с пользователем. Из его папки:

```powershell
npm.cmd ci
Copy-Item .env.example .env.local
npm.cmd run dev
```

Откройте [GraphQL-страницу](http://127.0.0.1:3000/my-courses), [REST-страницу](http://127.0.0.1:3000/my-courses-rest), [каталог](http://127.0.0.1:3000/courses). `API_URL=http://127.0.0.1:8000` читается сервером Next.js. `npm.cmd run build` успешно собирает проект; обе страницы отмечены `ƒ Dynamic`.

Полный запуск повторён на отдельной **пустой** базе `course_catalog_lab8_clean`: обе миграции, seed, проверки и временный API на 8008. Результаты — [evidence/clean-start.txt](evidence/clean-start.txt). Учебные `.env` и `.env.local`, окружения и зависимости не входят в Git. `change-me` — демонстрационный пароль.

## 2. Что изменилось в API

- `services.py` содержит `create_student`, `enroll`, `like_course` и `ServiceError(code, message)`. Имена ограничений преобразуются в коды правил. После IntegrityError выполняется rollback; неизвестное нарушение остаётся серверной ошибкой.
- `problem.py` переводит сервисные ошибки в RFC 9457: `application/problem+json`, поля `type`, `title`, `status`, `detail`, `instance`. Повторный email/запись дают 409, отсутствующий курс/студент — 404. Неизвестный маршрут и неверный HTTP-метод также используют Problem Details; для 405 сохраняется Allow. В обязательной части задания Pydantic 422 сохраняет стандартный формат FastAPI.
- `/graphql` принимает запросы и мутации. GraphiQL — браузерный редактор для работы с тем же endpoint. В ответах ID сериализуется строкой, имена полей — camelCase.
- Queries: `courses(isElective, limit)`, `course(id)`, `students(limit)`, `student(id)`, `enrollments(limit)`. Типы Course, Student и Enrollment позволяют выбирать вложенные связи.
- Mutations: `enroll(input: EnrollInput!)` и `likeCourse(id: ID!)`. Ожидаемые ошибки находятся в `data.<mutation>.userErrors`; ошибки схемы/исполнения — в верхнем `errors`. Успешный HTTP 200 сам по себе не гарантирует успех GraphQL.
- Каждому HTTP-запросу соответствует своя Session и свои четыре DataLoader. Кэш списков очищается после enroll, кэш курсов после likeCourse, чтобы последующие поля той же мутации видели изменения.
- `counter.py` считает события `before_cursor_execute` и помещает число в `X-SQL-Queries`. Счётчик ContextVar содержит изменяемый список, общий для задач и worker threads одного запроса. BEGIN/COMMIT не считаются отдельными событиями этого инструмента.
- Защита: максимальная глубина 5, не более 10 aliases, limit от 1 до 100, разбор числового ID, маскировка неожиданных исключений. Большой числовой ID намеренно демонстрирует второй слой: ошибка bigint остаётся в логе, клиент видит `Unexpected error.`.
- `GRAPHQL_INTROSPECTION=true` включена для GraphiQL. При false introspection отклоняется, обычные запросы работают. После изменения `.env` нужен перезапуск. Проверка: `try_protection.py --introspection-off`.
- Добавлены `GET /students/{id}` и `GET /students/{id}/enrollments`. Первый даёт 404 для неизвестного студента, второй возвращает отфильтрованный список (пустой при отсутствии записей).

Синхронные обращения SQLAlchemy в GraphQL пока выполняются в event loop, как в задании. Для долгих запросов нужен отдельный дизайн с AsyncSession; одну Session нельзя одновременно использовать из нескольких потоков. Ограничения глубины и aliases не заменяют авторизацию или rate limiting — они не входят в обязательную часть этой работы.

## 3. Примеры запросов

В GraphiQL, Variables: `{"id":"2"}`.

```graphql
query MyCourses($id: ID!) {
  student(id: $id) {
    name
    enrollments { id course { title credits level } }
  }
}
```

Ответ содержит Daniyar Bekov и три курса: Modern Frontend, Backend Foundations, AI/LLM Integration; каждый по 5 кредитов. Уровни intermediate, intermediate, beginner.

```graphql
mutation Enroll($input: EnrollInput!) {
  enroll(input: $input) {
    enrollment { id course { title } }
    userErrors { code message }
  }
}
```

Variables: `{"input":{"courseId":"web-security","studentId":"3"}}`. На исходных данных первый запрос успешен (id выдаёт база и он может отличаться):

```json
{"data":{"enroll":{"enrollment":{"id":"7","course":{"title":"Web Security Essentials"}},"userErrors":[]}}}
```

Повторный запрос:

```json
{"data":{"enroll":{"enrollment":null,"userErrors":[{"code":"ALREADY_ENROLLED","message":"Student is already enrolled in this course"}]}}}
```

Другие примеры:

```graphql
query Electives { courses(isElective: true, limit: 2) { id title level } }
mutation Like { likeCourse(id: "api-design") { course { id likes } userErrors { code message } } }
```

GET с читающим query разрешён, GET с mutation отклоняется HTTP 400 до SQL. Для изменения данных используйте POST.

## 4. REST и GraphQL — измеренное сравнение

Экран студента 2 на начальном наборе. `measure.py` суммирует байты тел ответов, без HTTP-заголовков; время не подменяется количеством запросов. Данные ответов двух вариантов дополнительно сравниваются.

| Критерий | REST | GraphQL | Источник |
|---|---|---|---|
| HTTP-запросы и раунды | 5 запросов, 2 раунда | 1 запрос, 1 раунд | measure.py |
| Байты ответов | 1145 | 339 | measure.py; размер времени enrolledAt может немного менять REST |
| SQL на экран | 5 | 3 | сумма X-SQL-Queries |
| Рост при 3 → 20 студентах | GET /enrollments с JOIN остаётся одним SQL, но конкретный экран требует запрос на каждый курс | До loader: 7/7 → 27/24; после: 3/3 → 3/3 | try_n_plus_1.py, experiment 4 |
| Ошибка текста запроса | 404 неизвестного адреса, 422 неверных параметров | HTTP 200, data:null и errors; gql обязан проверить errors | experiments 1, 8 |
| Повторная запись | 409, Problem Details, type …/already-enrolled | HTTP 200, userErrors: ALREADY_ENROLLED | services.py, experiment 3 |
| HTTP-кэш | GET-ресурсы можно кэшировать по URL с подходящими заголовками | POST обычно не кэшируется обычными HTTP-кэшами; GET-query допускает кэширование при явной политике | теория; в обеих страницах стоит no-store, измерения кэша не проводились |
| Дорогие запросы | Форму запроса задаёт маршрут, page_size ограничен 100 | Нужны проверки глубины, aliases и аргументов; 12 likes отвергаются с 0 SQL | experiment 6 |

Для простого каталога оставлю REST: один список получается одним запросом и контракт легко читать. Для вложенного персонального экрана выберу GraphQL: в измеренном примере 1 HTTP-запрос вместо 5 и 339 байт вместо 1145. Выигрыш зависит от конкретных маршрутов: REST также можно расширить отдельным агрегирующим endpoint. DataLoader нужен для контроля SQL-нагрузки независимо от количества HTTP-запросов.

## 5. Журнал восьми экспериментов

Наблюдения сохранены в [backend.json](evidence/backend.json), [frontend.json](evidence/frontend.json). Ошибочные варианты Python выполнялись в отдельной копии через FastAPI TestClient; остальные backend-проверки — через HTTP к Uvicorn. Эксперимент 8 выполнялся на настоящем Next.js dev server с временными изменениями файлов и восстановлением. Данные после опытов возвращены к 6/3/6.

| № | Что изменил | Что увидел | Причина | Исправление |
|---|---|---|---|---|
| 1 | titel вместо title; is_elective вместо isElective | HTTP 200, data:null, ошибки Cannot query field / Unknown argument с подсказками | Запрос не соответствует GraphQL-схеме; проверка до SQL | Правильные имена, проверка errors в клиенте |
| 2 | Убрал `CourseType | None` у course | Cannot return null for non-nullable field Query.course; data:null даже при успешном соседнем alias a | Null поднимается до ближайшего nullable-родителя; здесь до data | Возвращена nullable-аннотация: a сохранён, b:null |
| 3 | Отправил likeCourse через GET | HTTP 400, mutations are not allowed when using GET; SQL 0, likes остался 11. POST дал 12 | GET предназначен для чтения | POST; затем seed |
| 4 | Увеличил число студентов с 3 до 20 | Lazy: 7/7 → 27/24 SQL. DataLoader: 3/3 на обоих наборах | Отдельные lazy-запросы на связи; identity map уменьшает повторы курсов, но не устраняет N+1 | Пакетная загрузка связей, затем seed |
| 5 | Batch-функция вернула строки в ORDER BY column DESC без группировки | Первый запрос: expected 3, received 6. Второй: без errors, но 4 из 6 записей получили неверный курс | Длина результата должна совпадать с keys; одинаковая длина не гарантирует порядок | Словарь groups по значению ключа; результат собирается в порядке keys |
| 6 | Шесть опасных запросов и 12 мутаций до/после защиты | До: исполнялись глубина/aliases, раскрывались исключения. После: понятные ошибки аргументов, маскировка внутренних; flood — 0 SQL | Клиент управляет формой запроса; одних HTTP-ограничений мало | QueryDepthLimiter, MaxAliasesLimiter, check_limit, parse_id, MaskErrors |
| 7 | GRAPHQL_INTROSPECTION=false | __schema запрещён; обычный course работает; опечатка cours всё ещё даёт Did you mean course/courses | Отключение карты схемы не скрывает поля и не является авторизацией | Вернул true для GraphiQL |
| 8 | Опечатка в query; удалённая проверка errors; API остановлен | GraphQLRequestError с причиной; TypeError Cannot destructure … null; TypeError fetch failed | Ошибка GraphQL, потерянная причина, отсутствие сетевого ответа — разные ситуации | Восстановлены query и проверка errors, API запущен |

Числа N+1: students → enrollments → course = 1 + N + число разных курсов, то есть 1+3+3=7 и 1+20+6=27. Для enrollments → course, student: 1+3+3=7 и 1+6+17=24. Во втором запросе LIMIT 20 возвращает 20 из 23 записей, принадлежащих 17 студентам. После loader оба запроса выполняют три SQL, а запрос только за именами студентов — один.

Неверный batch с подходящей длиной опаснее исключения: ответ формально успешен, но связывает данные неверно. Для отсутствующего ключа single-loader возвращает None, many-loader — пустой список; позиция ключа сохраняется.

| Проверка защиты | До | После |
|---|---|---|
| Цикл глубины 6 | Выполнился | exceeds maximum operation depth of 5 |
| 12 aliases | Выполнились | 12 aliases found. Allowed: 10 |
| limit -1 | InvalidRowCountInLimitClause, SQL и параметры | limit must be between 1 and 100 |
| ID abc | Текст ValueError | Invalid ID: 'abc' |
| ID из 20 цифр | NumericValueOutOfRange, таблица и SQL | Unexpected error. |
| Introspection | Схема доступна | Доступность зависит от GRAPHQL_INTROSPECTION |

Без защиты 12 likeCourse увеличили likes 11 → 23 и выполнили **12 SQL**. Это отличается от 24 в примере задания: в нашем проекте ещё с Lab 7 установлен `expire_on_commit=False`, а UPDATE … RETURNING уже возвращает курс, поэтому дополнительный SELECT после commit не нужен. С защитой те же 12 aliases дают **0 SQL**, likes остаётся 11 на восстановленном наборе.

Без маскировки клиент узнавал названия таблиц/колонок, SQL, параметры и тип драйверного исключения; ValueError раскрывал способ преобразования ID. Проверки аргументов позволяют исправить запрос, тогда как универсальное Unexpected error не объясняет, какое значение неверно. Если уменьшить max_depth до 2, законный MyCourses (student → enrollments → course, глубина 3) перестаёт проходить; это проверено отдельно. Запрос глубины 4 при настройке 5 проходит.

Особенность фактического frontend-эксперимента: Next.js 16 с `loading.tsx` начинает streaming-ответ, поэтому внешний HTTP-статус страницы был **200**, а ошибки появлялись в серверном логе и error boundary. В примере задания показан 500 для нестримингового ответа. Наши реальные статусы и сообщения сохранены в frontend.json; GraphQL-ответ с ошибкой query тоже имел 200.

## 6. Решения

1. **Правила в services.py.** Два транспорта вызывают одну реализацию и получают одинаковый код ошибки. Если проверять отдельно в REST и GraphQL, изменения легко применить только к одной версии. REST переводит код в HTTP/Problem Details, GraphQL — в userErrors. Атомарное увеличение лайков и обработка ограничений остаются общими.
2. **Loader на один запрос и сопоставление по ключам.** Глобальный кэш пережил бы запрос и мог вернуть устаревшие данные или данные другого пользователя после добавления авторизации. Порядок SQL-строк не обязан совпадать с порядком keys: эксперимент 5 дал четыре неверных курса без ошибки. Поэтому каждая Context создаёт свои loaders, а batch собирает ответ через groups[key].
3. **Два слоя защиты.** check_limit и parse_id дают понятные сообщения для ожидаемых ошибок ввода до лишней работы базы. MaskErrors скрывает непредвиденные исключения, сохраняя подробности в серверном логе. Он не должен маскировать ошибки схемы и наши GraphQLError, иначе клиент потеряет полезную причину отказа.

Дополнительные проверки: оба последовательных enroll в одном GraphQL-запросе видят актуальный список студента (2, затем 3 записи); кэш очищается после успешной мутации. POST с повторной записью не оставляет сессию в аварийном состоянии. Модели и обе миграции Lab 7 не изменены.

Документация библиотек: [Strawberry DataLoaders](https://strawberry.rocks/docs/guides/dataloaders), [Next.js fetch](https://nextjs.org/docs/app/api-reference/functions/fetch). В истории Git сохранены отдельные этапы: services, endpoint, типы, мутации, счётчик, DataLoaders, исправление инвалидации, защита, REST-сравнение и отчёт.
