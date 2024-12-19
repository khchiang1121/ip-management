# https://www.pythonkitchen.com/how-implement-beautiful-notifications-flask/
# https://www.1ju.org/flask/flask-message-flashing

# 把這個放在main的最一開始
# <div id="flashed-messages" style="position: fixed; right: 1%;bottom: 1%; z-index:999;">
# 	{% with messages = get_flashed_messages() %}
# 	  {% if messages %}
# 		{% for message in messages %}
# 		  {{ message | safe}}
# 		{% endfor %}
# 	  {% endif %}
# 	{% endwith %}
# </div>
def notify(message, alert_type="primary"):
    """
    Used with flash
        flash(notify('blabla'))

    Parameters
    ----------
    message: str
        message to be displayed

    alert_type: str
        bootstrap class

    Returns
    -------
    None
    """
    alert = """
    <div class="shopyo-alert alert alert-{alert_type} alert-dismissible fade show" role="alert"
        style="opacity: 0.9;">
      {message}

      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close">
        <!-- <span aria-hidden="true">×</span> -->
      </button>
    </div>
    """.format(
        message=message, alert_type=alert_type
    )

    scriptFade = """ 
    <script>
          setTimeout(function() {
            $('#flashed-messages').fadeOut(500);
        }, 5000); // <-- time in milliseconds (5 secs)
    </script>
    """
    return alert + scriptFade


def notify_success(message):
    return notify(message, alert_type="success")


def notify_danger(message):
    return notify(message, alert_type="danger")


def notify_warning(message):
    return notify(message, alert_type="warning")


def notify_info(message):
    return notify(message, alert_type="info")