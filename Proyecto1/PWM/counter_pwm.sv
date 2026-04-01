//Incrementando el contador en cada flanco positivo del clock

module counter_pwm(
    input clk,
    input rst_n,
    output reg [7:0] count
);

always @(posedge clk or negedge rst_n) begin //Cada vez que el clock hace “tic”
    if (!rst_n) //Si reset está activo
        count <= 0;
    else
        count <= count + 1; //Aumentando contador
end

endmodule