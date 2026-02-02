#include <Servo.h>

Servo servos[18];
int speed=300;

// Define the pins for each servo
const int servoPins[18] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 21};
char command; 
char direction='a';
// Define the initial angles for each servo
const int initialAngles[18] = {
  90, 158, 145, // L1, L2, L3
  90, 160, 145, // L4, L5, L6
  90, 160, 140, // L7, L8, L9
  90, 140, 140, // R1, R2, R3
  90, 150, 140, // R4, R5, R6
  90, 165, 145  // R7, R8, R9
};

void setup() {
  // Initialize the Serial Monitor communication
  Serial.begin(115200);
 
  // Initialize Serial1 for communication with the HC-05 module
  Serial1.begin(115200);
 
  Serial.println("Bluetooth communication setup complete.");

 // Attach each servo to a pin
  for (int i = 0; i < 18; i++) {
    servos[i].attach(servoPins[i]);
  }

  // Move all servos to their initial positions
  for (int i = 0; i < 18; i++) {
    servos[i].write(initialAngles[i]);
  }
  delay(1000);  // Wait for servos to reach their initial positions

}

void loop() {

  if (Serial1.available()) {
    String data  = Serial1.readString();
    // Trim leading and trailing whitespace from the received data
    data.trim();

    Serial.println("data"+data);
    Serial.println(data.length());
    // Process each character in the data string
    for (int i = 0; i < data.length(); i++) {
      char command = data.charAt(i);
      Serial.println(command);
      switch(command) {
        case 'F':
          direction = 'F';
          Serial.println("Forward");
          break;
        case 'B':
          direction='B';
          Serial.println("Backward");
          break;
        case 'L':
          direction='L';
          Serial.println("Left");
          break;
        case 'R':
          direction='R';
          Serial.println("Right");
          break;
        case 'S':
          direction='S';
          break;
        default:
          direction='S';
          // Handle unexpected characters
          Serial.print("Unknown command: ");
          // Serial.println(command);
          break;
      }
    }
  }
  switch(direction){
        case 'F':
          move_forward();
          Serial.println("Forward");
          break;
        case 'B':
          move_backward();
          Serial.println("Backward");
          break;
        case 'L':
          turn_left();
          Serial.println("Left");
          break;
        case 'R':
          turn_right();
          Serial.println("Right");
          break;
  }
}

void move_forward() {
  // Step 1
  servos[1].write(180);
  servos[2].write(90);
  servos[7].write(180);
  servos[8].write(90);
  servos[13].write(180);
  servos[14].write(90);
  delay(speed);
  Serial.println("step1");

  // Step 2
  servos[0].write(120);
  servos[6].write(120);
  servos[12].write(60);
  delay(speed);
  Serial.println("step2");

  // Step 3
  servos[1].write(158);
  servos[2].write(145);
  servos[7].write(160);
  servos[8].write(140);
  servos[13].write(150);
  servos[14].write(140);
  delay(speed);
  Serial.println("step3");

  // Step 4
  servos[0].write(90);
  servos[6].write(90);
  servos[12].write(90);
  servos[4].write(180);
  servos[5].write(90);
  servos[10].write(180);
  servos[11].write(90);
  servos[16].write(180);
  servos[17].write(90);
  delay(speed);
  Serial.println("step4");


  // Step 5
  servos[3].write(120);
  servos[9].write(60);
  servos[15].write(60);
  delay(speed);
  Serial.println("step5");


  // Step 6
  servos[4].write(160);
  servos[5].write(145);
  servos[10].write(145);
  servos[11].write(150);
  servos[16].write(165);
  servos[17].write(145);
  delay(speed);
  Serial.println("step6");


  // Step 7
  servos[3].write(90);
  servos[9].write(90);
  servos[15].write(90);
  servos[1].write(180);
  servos[2].write(90);
  servos[7].write(180);
  servos[8].write(90);
  servos[13].write(180);
  servos[14].write(90);
  Serial.println("step6");

}

void move_backward() {
      // Step 1
  servos[1].write(180);
  servos[2].write(90);
  servos[7].write(180);
  servos[8].write(90);
  servos[13].write(180);
  servos[14].write(90);
  delay(speed);

  // Step 2
  servos[0].write(60);
  servos[6].write(60);
  servos[12].write(120);
  delay(speed);

  // Step 3
  servos[1].write(158);
  servos[2].write(145);
  servos[7].write(160);
  servos[8].write(140);
  servos[13].write(150);
  servos[14].write(140);
  delay(speed);

  // Step 4
  servos[0].write(90);
  servos[6].write(90);
  servos[12].write(90);
  servos[4].write(180);
  servos[5].write(90);
  servos[10].write(180);
  servos[11].write(90);
  servos[16].write(180);
  servos[17].write(90);
  delay(speed);

  // Step 5
  servos[3].write(60);
  servos[9].write(130);
  servos[15].write(120);
  delay(speed);

  // Step 6
  servos[4].write(160);
  servos[5].write(145);
  servos[10].write(145);
  servos[11].write(150);
  servos[16].write(165);
  servos[17].write(145);
  delay(speed);

  // Step 7
  servos[3].write(90);
  servos[9].write(90);
  servos[15].write(90);
  servos[1].write(180);
  servos[2].write(90);
  servos[7].write(180);
  servos[8].write(90);
  servos[13].write(180);
  servos[14].write(90);
}

void turn_left() {
  
  // Step 1
  servos[1].write(180);
  servos[2].write(90);
  servos[7].write(180);
  servos[8].write(90);
  servos[13].write(180);
  servos[14].write(90);
  delay(speed);

  // Step 2
  servos[0].write(60);
  servos[6].write(60);
  servos[12].write(60);
  delay(speed);

  // Step 3
  servos[1].write(158);
  servos[2].write(145);
  servos[7].write(160);
  servos[8].write(140);
  servos[13].write(150);
  servos[14].write(140);
  delay(speed);

  // Step 4
  servos[0].write(90);
  servos[6].write(90);
  servos[12].write(90);
  servos[4].write(180);
  servos[5].write(90);
  servos[10].write(180);
  servos[11].write(90);
  servos[16].write(180);
  servos[17].write(90);
  delay(speed);

  // Step 5
  servos[3].write(60);
  servos[9].write(60);
  servos[15].write(60);
  delay(speed);

  // Step 6
  servos[4].write(160);
  servos[5].write(145);
  servos[10].write(135);
  servos[11].write(150);
  servos[16].write(165);
  servos[17].write(145);
  delay(speed);

  // Step 7
  servos[3].write(90);
  servos[9].write(90);
  servos[15].write(90);
  servos[1].write(180);
  servos[2].write(90);
  servos[7].write(180);
  servos[8].write(90);
  servos[13].write(180);
  servos[14].write(90);
  
}

void turn_right() {
  // Step 1
  servos[1].write(180);
  servos[2].write(90);
  servos[7].write(180);
  servos[8].write(90);
  servos[13].write(180);
  servos[14].write(90);
  delay(speed);

  // Step 2
  servos[0].write(120);
  servos[6].write(120);
  servos[12].write(120);
  delay(speed);

  // Step 3
  servos[1].write(158);
  servos[2].write(145);
  servos[7].write(160);
  servos[8].write(140);
  servos[13].write(150);
  servos[14].write(140);
  delay(speed);

  // Step 4
  servos[0].write(90);
  servos[6].write(90);
  servos[12].write(90);
  servos[4].write(180);
  servos[5].write(90);
  servos[10].write(180);
  servos[11].write(90);
  servos[16].write(180);
  servos[17].write(90);
  delay(speed);

  // Step 5
  servos[3].write(120);
  servos[9].write(120);
  servos[15].write(120);
  delay(speed);

  // Step 6
  servos[4].write(160);
  servos[5].write(145);
  servos[10].write(135);
  servos[11].write(150);
  servos[16].write(165);
  servos[17].write(145);
  delay(speed);

  // Step 7
  servos[3].write(90);
  servos[9].write(90);
  servos[15].write(90);
  servos[1].write(180);
  servos[2].write(90);
  servos[7].write(180);
  servos[8].write(90);
  servos[13].write(180);
  servos[14].write(90);
  
}