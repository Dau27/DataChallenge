"""Conservative contradiction checks for the literal initial rubric.

These checks ask the provider to repair observable conflicts; they never assign a
score. They are not a multilingual semantic evaluator or organizer ground truth.
Only exact initial definitions/anchors/N/A conditions activate these checks.
"""
import re


RULES = {
    "needs": ("binary", "Да — оператор учёл известные детали и уточнил недостающее до ответа.",
              "Данных для ответа хватало с самого начала.", ()),
    "identification": ("binary", "Да — проверка личности подтверждена до раскрытия данных или защищённого действия.",
                       "Запрос не требовал идентификации.", ()),
    "consultation": ("scale", "Оцените ответ или следующий шаг по указанной шкале.",
                     "Чат закончился до того, как клиент сформулировал запрос.", (
                         (20, "Все существенные вопросы закрыты или дан корректный следующий шаг."),
                         (15, "Основной вопрос решён, пропущена второстепенная деталь."),
                         (10, "Часть запроса закрыта, существенный вопрос остался открытым."),
                         (5, "Есть общая подсказка, но клиенту всё ещё непонятно, как действовать."),
                         (0, "Ответа по существу нет или ключевая рекомендация ошибочна."))),
    "dialogue": ("scale", "Оцените ясность, порядок ответов и предупреждение об ожидании по указанной шкале.", None, (
        (10, "Ответы ясные и связные. Если было явное ожидание, оператор предупредил."),
        (7, "Один заметный сбой, но клиент может понять ответ и продолжить."),
        (4, "Клиенту приходится переспрашивать из-за формулировок или порядка ответов."),
        (0, "Из-за бессвязных или противоречивых реплик ход диалога непонятен."))),
    "closing": ("binary", "Да — оператор подвёл итог или предложил дальнейшую помощь и попрощался.",
                "Чат оборвался до возможности его завершить.", ()),
    "critical": ("flag", "Да — выявлено оскорбление клиента, предложение платной услуги в обход компании или раскрытие конфиденциальной информации. Нет — ни одно из трёх не выявлено.", None, ()),
}


def initial_rule(criterion):
    signature = (criterion.answer_type, criterion.description.strip(), criterion.na_condition,
                 tuple((a.value, a.description) for a in criterion.scale))
    return next((name for name, expected in RULES.items()
                 if signature == expected and criterion.na_allowed == (expected[2] is not None)), None)


def matches(pattern, text):
    return bool(re.search(pattern, text, re.I))


def _necessary_question(messages):
    # Only flag a new context slot when it was not already supplied before the
    # question and a later client turn actually answers. Identity is separate.
    slots = (
        (r"which (?:web)?site|қай (?:сайт|веб)|како[йм] (?:сайт|платформ)",
         r"https?://|www\.|\.(?:com|global|kz)\b|company (?:web)?site|компанияның сайты|сайт[еа]? компании"),
        (r"which currency|what currency|қай валюта|қандай валюта|како[йя] валют",
         r"\b(?:usd|eur|kzt|dollars?|euros?|tenge)\b|евро|еуро|доллар|теңге|рубл"),
    )
    for index, message in enumerate(messages):
        if message["speaker"] != "operator":
            continue
        before = " ".join(m["text"] for m in messages[:index] if m["speaker"] == "client")
        following = next((m for m in messages[index + 1:] if m["speaker"] in {"client", "operator"}), None)
        if not following or following["speaker"] != "client":
            continue
        if any(matches(question, message["text"]) and not matches(answer, before)
               and matches(answer, following["text"]) for question, answer in slots):
            return True
    return False


def _reask(messages):
    # Ordinary new questions, including 'where now?', do not establish a defect.
    for previous, current in zip(messages, messages[1:]):
        if previous["speaker"] != "operator" or current["speaker"] != "client":
            continue
        if matches(r"which other one|what do you mean by that|я (?:же )?про .{1,50} спрашиваю|"
                   r"дегеніңіз қалай|что (?:именно )?стоит\?.{0,35}какой раздел", current["text"]):
            return True
    return False


def _unverified_disclosure(messages):
    verified = False
    disclosure = False
    explicit_unverified = False
    for message in messages:
        text = message["text"]
        if message["speaker"] in {"operator", "system"} and matches(
                r"identity (?:has been |is )?(?:confirmed|verified)|verification (?:completed|confirmed)|"
                r"личность подтверждена|идентификаци[яю] (?:пройдена|подтверждена)|жеке басыңыз расталды", text):
            verified = True
        if message["speaker"] == "operator" and not verified and matches(
                r"your account (?:has|is subject to) (?:a )?(?:withdrawal )?(?:restriction|block)|"
                r"на вашем сч[её]те действует ограничение|сіздің шотыңызда .{0,30}шектеу", text):
            disclosure = True
        if message["speaker"] == "client" and matches(
                r"i (?:have not|haven't|did not|didn't) (?:yet )?(?:verified|verify|confirmed|confirm) (?:my )?identity|"
                r"я ещ[её] не подтверждал[аи]? личность|жеке басымды .{0,15}растаған жоқпын", text):
            explicit_unverified = True
    # Do not infer confidential access from general guidance or future checks.
    return disclosure and explicit_unverified


def _incorrect_rejection_claim(messages):
    for message in messages:
        if message["speaker"] != "operator":
            continue
        for clause in re.split(r"[.!?\n]", message["text"]):
            # Do not reject a correction such as 'rejected does NOT necessarily
            # mean executed', or a factual statement about a later status change.
            if matches(r"\b(?:not|never|doesn't|isn't)\b|\bне\b|емес|орындалып.{0,15}жоқ", clause):
                continue
            if matches(r"rejected.{0,45}(?:necessarily|always).{0,25}executed|"
                       r"қабылданбаса.{0,40}міндетті түрде орындалып|отклон.{0,35}обязательно исполнен", clause):
                return True
    return False


FAREWELL = r"goodbye|have a good (?:day|evening)|\bbye\b|до свидания|хорошего (?:дня|вечера)|сау болыңыз"
HELP = r"if you need anything else|further help|если .{0,35}(?:помощ|вопрос|подсказ)|басқа сұрақтарыңыз"
RECAP = r"no (?:further|additional) action.{0,20}(?:needed|required)|дополнительных действий от вас не нужно|we will follow up here"
OUTCOME = r"glad you (?:got in|found it)|рад[аы]?, что .{0,20}(?:вошли|нашли)"
COURTESY = r"(?:you're welcome|you are welcome|glad i could help|glad to help|happy to help|thanks|thank you|great|пожалуйста|спасибо|көмегім тигеніне қуаныштымын|оқасы жоқ|рақмет)"


def _courtesy_only(text):
    return not re.search(r"\w", re.sub(f"{FAREWELL}|{COURTESY}", "", text, flags=re.I))


def validate_initial_rubric(checklist, assessment, conversation):
    messages = conversation["transcript"]
    operators = [m for m in messages if m["speaker"] == "operator"]
    human_text = " ".join(m["text"] for m in operators)
    explanation_gap = r"(?<!no )unanswered|(?<!no )unresolved|not answered|not provided|не (?:был[аи]? )?(?:дан|отвечен|раскрыт)|не закрыл|остал.{0,20}открыт"
    unverified = _unverified_disclosure(messages)
    errors = []
    for criterion in checklist.criteria:
        rule = initial_rule(criterion)
        judgment = assessment.results[criterion.id]

        def reject(reason):
            errors.append(f"{criterion.id}: {reason}")

        if rule == "needs" and judgment.disposition == "not_applicable":
            no_request = any(m["speaker"] == "system" and matches(
                r"before .{0,30}(?:stat|ask|formulat).{0,15}(?:request|question)|сұрағын жазбай тұрып|до .{0,20}сформулировал", m["text"]) for m in messages)
            diagnostic_refused = matches(r"(?:ticker|тикер).{0,25}(?:not need|no need)|"
                                         r"тикерді қараудың қажеті жоқ|тикер .{0,15}проверять не нужно", human_text)
            if _necessary_question(messages) or no_request or diagnostic_refused:
                reject("initial sufficiency conflicts with observable missing-context clarification, no formulated request, or refusal of diagnostic checking. A clear topic is not sufficient detail; N/A cannot excuse an omitted clarification.")
        if rule == "dialogue" and judgment.disposition == "assessed" and judgment.value > 4 and _reask(messages):
            reject("a customer explicitly re-asks because of wording/order; the saved re-asking anchor is 4, not 7 or 10. A later repair does not erase the earlier disruption.")
        if rule in {"identification", "critical"} and unverified:
            wrong = (judgment.disposition == "not_applicable" or judgment.disposition == "assessed" and judgment.value is True) if rule == "identification" else judgment.disposition == "assessed" and judgment.value is False
            if wrong:
                reject("an account-specific restriction was disclosed before verification and the customer explicitly confirms they had not verified identity. Check identification and the separate confidential-disclosure flag independently.")
        if rule == "consultation" and judgment.disposition == "assessed":
            reason = judgment.explanation
            gap = matches(explanation_gap, reason) and not matches(r"\bno\b[^.;]{0,40}\b(?:unanswered|unresolved)\b", reason)
            if judgment.value == 20 and gap:
                reject("maximum consultation contradicts the explanation's unanswered request. Deferring a question does not retract it; distinguish a minor secondary omission from a material gap.")
            if judgment.value != 0 and _incorrect_rejection_claim(messages):
                reject("the key recommendation asserts that rejection necessarily means execution; the incorrect-key-recommendation anchor is 0, not partial credit.")
            if judgment.value in {5, 10, 15} and matches(r"off.company|bypass.{0,15}company|personal money transfer|в обход компании|жеке аудар", reason) and not gap:
                reject("partial consultation is attributed to an unrelated off-company offer without identifying an unanswered customer request. Keep critical misconduct separate and name a genuine consultation gap or use the complete-answer anchor.")
        if rule == "closing" and judgment.disposition == "assessed" and operators:
            final = operators[-1]["text"]
            explicit = matches(HELP + "|" + RECAP, final)
            last_client = next((m for m in reversed(messages[:messages.index(operators[-1])]) if m["speaker"] == "client"), None)
            confirmed = matches(OUTCOME, final) and last_client and matches(
                r"that worked|(?:i |i've )?(?:got in|found it)|наш[её]л|получилось", last_client["text"])
            if judgment.value is False and matches(FAREWELL, final) and (explicit or confirmed):
                reject("the final human response contains an explicit recap/help offer plus farewell. A specific confirmed outcome or no-further-action recap satisfies the recap branch; a separate help offer is not required.")
            if judgment.value is True and _courtesy_only(final) and not any(matches(HELP + "|" + RECAP + "|" + OUTCOME, m["text"]) for m in operators[:-1]):
                reject("final courtesy/farewell has no recap or explicit further-help offer; citing an earlier ordinary answer cannot supply a missing closing component.")
    if errors:
        raise ValueError("; ".join(errors) + " Re-read the full source and repair all listed conflicts using the saved definitions; do not invent evidence or change unrelated criteria.")
