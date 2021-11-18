function Convert(n1, n2, conversion_factor) {
    // id's for currency input boxes
    id1 = "cb" + n1; 
    id2 = "cb" + n2;

    // getting the value of the input box that just got filled
    var input_box = document.getElementById(id1).value;

    // updating the other input box after conversion
    document.getElementById(id2).value = ((input_box * conversion_factor).toFixed(2));
}