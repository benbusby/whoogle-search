const convert = (n1, n2, conversionFactor) => {
    // id's for currency input boxes
    let id1 = "cb" + n1; 
    let id2 = "cb" + n2;
    // getting the value of the input box that just got filled
    let inputBox = document.getElementById(id1).value;
    // updating the other input box after conversion
    document.getElementById(id2).value = ((inputBox * conversionFactor).toFixed(2));
}
