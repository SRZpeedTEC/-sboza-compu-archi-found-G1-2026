//Decidiendo si la salida debe ser 1 o 0

module comparator_pwm(
    input [7:0] count,
    input [7:0] duty,
    output pwm_out
);

//Si el contador es menor al porcentaje al que quiero llegar entonces se colocan los 1s, de lo contrario los 0s (11110000)
assign pwm_out = (count < duty);

endmodule