
function createForumTopic() {
    let $schedForm = $("#forum_topic_form"),
        formIsValid = $schedForm[0].checkValidity();

    if (!formIsValid || formIsValid === false) {
        $schedForm.removeClass("needs-validation").addClass("was-validated");
    } else {
        $.ajax({
            url: "/a/forum_topic/create/",
            data: $schedForm.serialize(),
            type: "POST",
            success: function (data) {
                if (data.isValid) {
                    // Show success alert in forum div
                    $("#forum_topic_alert").text(data.msg)
                        .removeClass("d-none")
                        .addClass("alert-success");
                    setTimeout(function() {
                        $("#forum_topic_alert")
                            .empty()
                            .addClass("d-none")
                            .removeClass("alert-success");
                    }, 1000);
                    resetForm("forum_topic_alert");
                }
                else {
                    // showAppAlert("warning", data.msg, {"body": JSON.stringify(data.errors)});
                    let errs = JSON.parse(data.errors);

                    console.log(errs);
                    $("#forum_topic_alert").text(JSON.stringify(data.errors))
                        .removeClass("d-none")
                        .addClass("alert-warning");
                    setTimeout(function() {
                        $("#forum_topic_alert")
                            .empty()
                            .addClass("d-none")
                            .removeClass("alert-warning");
                    }, 2100);
                    console.log(data.nonFieldErrors);
                }
            },
            fail: function (data) {
                $("form").html(
                    '<div class="alert alert-danger">Could not reach server, please try again later.</div>'
                );
            }
        });
    }
}


$(function() {
    $('#forum_topic_form').submit(function(event) {
        event.preventDefault();
        event.stopPropagation();
    });

});