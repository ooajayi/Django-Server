function resetForm(form){
    $('#'+form).find("input[type=text],input[type=email],input[type=password],input[type=file],textarea ").each(function(){
        $(this).val('');
    });
}

function showAppAlert(alertType, msg_header, opts) {
    opts = opts || {}
    let _msg_header = msg_header || null,
        _msg_body = opts.msg_body || null,
        displayDur = opts.duration || 10000;

    $("#dcc_msg_alert")
        .removeClass("d-none")
        .removeClass("alert-primary")
        .removeClass("alert-secondary")
        .removeClass("alert-success")
        .removeClass("alert-warning")
        .removeClass("alert-danger")
        .removeClass("alert-light")
        .removeClass("alert-dark")
        .addClass("alert-" + alertType);

    if (_msg_header) {
        $("#dcc_msg_alert .alert-heading")
            .removeClass("d-none").empty().text(_msg_header);
    } else $("#dcc_msg_alert .alert-heading").addClass("d-none");
    
    if (_msg_body) {
        $("#dcc_msg_alert #msg_body")
            .removeClass("d-none").empty().text(_msg_body);
    } else $("#dcc_msg_alert #msg_body").addClass("d-none");

    setTimeout(function(){
        $("#dcc_msg_alert").addClass("d-none");
    }, displayDur);
}

function validateYear(year, ev) {
    var text = /^[0-9]+$/;
    if (ev.type ==="blur" || year.length=== 4 && ev.keyCode!== 8 && ev.keyCode!== 46) {
        if (year !== 0) {
            if ((year !== "") && (!text.test(year))) {
                alert("Please Enter Numeric Values Only");
                return false;
            }
  
            if (year.length !== 4) {
                alert("Year is not proper. Please check");
                return false;
            }
            var next_year = new Date().getFullYear() + 1;
            if ((year < 1920) || (year > next_year)) {
                alert("Year should be in range 1920 to " + next_year);
                return false;
            }
            return true;
        }
    }
    return false;
}


function isMobile() {
    if (window.matchMedia("(max-width: 767px)").matches){ 
        // The viewport is less than 768 pixels wide
        return true;
    } else {
        // The viewport is at least 768 pixels wide
        return false;
    }
}
