# **Проект "GoldRunnerGame"**

Данный проект реализовывает 2D-платформер, в котором цель игры собрать все монеты на каждом уровне,
не попавшись в лапы зомби.

В стартовом окне вы можете посмотреть доску лидеров, а также окно с правилами игры и кнопками управления.
Также в стартовом окне вы можете начать игру, выбрав режим игры (1 игрок/2 игрока)

После старта вы появитесь на 1 уровне. Цель игры — собирать монеты. Вас будет преследовать зомби, который двигается по самому короткому пути к вам,
Мы должны убегать от него (и от игрока, играющего за зомби).

На каждом уровне появляется на 1 монету больше, чем надо, чтобы игрок, играющий за зомби не мог прибегать к нечестной тактике
(просто караулить последнюю монету). Зомби в игре сталкиваются друг с другом (для достижения большей реалистичности).
Также в игре присутствуют различные интересные механики и трюки, которые можно узнать только опытным путем
(например некоторые места, где боты могут зажать игрока, или наоборот, места, где игрок может разорвать дистанцию с ботами. А также ловушки, из которых вы не выберетесь).

В конце второго уровня прописан скрипт, генерирующий лопату, с которой можно копать ветхие стены. Скрипт прописан так, что игрок не завершит 2 уровень, не собрав все лопаты.
Лопата во 2 уровне заменяет монету.

После прохождения последнего (3 уровня), появляется победное окно, в котором виден итоговый результат и поле для ввода имени для сохранения результата в бд.
Игру можно ставить на паузу (клавиша P) или выходить форсированно (клавишу ESC). После поражения или победы вы возвращаетесь в главное меню, где вы можете снова начать игру.

###### _Примечание_
Вы можете уменьшить количество монет на каждом уровне в файлах в папке levels (во второй строке), чтобы вам было проще пройти игру и оценить весь ее функционал
Также для игры рекомендуется размер экрана не меньше 1600x1200, однако если таковой возможности нет,
то вы можете уменьшить размер тайлов в файле constants.py (переменная TILE_SIZE). (Оптимальные варианты: 35, 40 (стандартный))
