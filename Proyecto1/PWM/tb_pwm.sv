module tb_pwm;

reg clk, rst_n;
reg [2:0] pwm_level;
wire pwm_out;

pwm_top dut(clk, rst_n, pwm_level, pwm_out);

always #5 clk = ~clk; //Simula el reloj de la FPGA, espera 5 unidades de tiempo y lo invierte

//Imprime cada vez que algo cambia
initial begin
    $monitor("Tiempo=%0t | clk=%b | rst_n=%b | pwm_level=%b | duty=%d | count=%d | pwm_out=%b",
              $time,
              clk,
              rst_n,
              pwm_level,
              dut.duty,   // acceso interno
              dut.count,  // acceso interno
              pwm_out);
end

initial begin
    clk = 0;
    rst_n = 0; //Activo
    pwm_level = 3'b000; //0%
	 
	 $display("---- INICIO SIMULACION ----");

    #10 rst_n = 1; //Después de 10 unidades de tiempo reset se desactiva
	 $display("Se desactiva reset");

    #50 pwm_level = 3'b001; // 25%
	 $display("Cambio a 25%%");
	 
    #50 pwm_level = 3'b010; // 50%
	 $display("Cambio a 50%%");
	 
    #50 pwm_level = 3'b011; // 75%
	 $display("Cambio a 75%%");
	 
    #50 pwm_level = 3'b100; // 100%
	 $display("Cambio a 100%%");

    #100 
	 $display("---- FIN SIMULACION ----");
	 $finish; //Después de 100 unidades de tiempo se detiene todo
end

endmodule