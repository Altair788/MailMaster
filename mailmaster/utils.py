def check_sends(successful_sends_count: int, recipient_list):
    status = ""
    response = ""
    if successful_sends_count == len(recipient_list):
        # Все письма отправлены успешно
        status = "success"
        response = f"Успешно отправлено всем получателям: {successful_sends_count}/{len(recipient_list)}"
    elif successful_sends_count > 0:
        # Часть писем отправлена успешно
        status = "partial_success"
        response = (
            f"Отправлено {successful_sends_count} из {len(recipient_list)} получателей"
        )
    elif successful_sends_count == 0:
        # Ни одно письмо не отправлено
        status = "failed"
        response = "Не удалось отправить ни одного письма"

    return status, response
