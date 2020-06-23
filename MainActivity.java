package com.strawhat.eden;

import android.content.DialogInterface;
import android.support.v7.app.AlertDialog;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

//Paho MQTT libraries
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttMessage;

import helpers.MQTThelper;


public class MainActivity extends AppCompatActivity {
    private static final String TAG = "MainActivity";

    MQTThelper mqttHelper;
    TextView condition,water;
    String data, email="";
    EditText input;
    com.github.lzyzsd.circleprogress.CircleProgress pcircle;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
		//Links the GUI controls to the referece variables
		setContentView(R.layout.activity_main);
        condition = (findViewById(R.id.txtCondition));
        water = (findViewById(R.id.txtWater));
        pcircle = (findViewById(R.id.pCircle));
        Button btnSync = (findViewById(R.id.btnSync));
        Button btnPicture = (findViewById(R.id.btnPicture));
        Button btnOn = (findViewById(R.id.btnOn));

		//Start MQTT client
        startMqtt();

		//Popup window for the user to enter his email
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Email");
        builder.setIcon(R.drawable.ic_launcher_background);
        builder.setMessage("Please enter your email:");
        input = new EditText(this);
        builder.setView(input);

		//Ok button event
        builder.setPositiveButton("Submit", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                email = input.getText().toString();
                Toast.makeText(getApplicationContext(),email,Toast.LENGTH_LONG).show();


                mqttHelper.Publish("GPIO/instructions",email);
                Log.i(TAG,"Email taken!");
            }
        });

		//Cancel buttonn event
        builder.setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                dialog.dismiss();
            }
        });

        final AlertDialog ad =builder.create();


		//Click events for the main GUI buttons
        btnSync.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {

                ad.show();

            }
        });

        btnPicture.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                mqttHelper.Publish("GPIO/instructions","picture");
                Log.i(TAG,"Picture taken!");
            }
        });

        btnOn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                mqttHelper.Publish("GPIO/instructions","pump");
                Log.i(TAG,"System is ON!");
            }
        });


    }

	//MQTT helper
    private void startMqtt() {
		
		//Creates helper object
        mqttHelper = new MQTThelper(getApplicationContext());
        mqttHelper.setCallback(new MqttCallbackExtended() {
            @Override
            public void connectComplete(boolean b, String s) {

            }

            @Override
            public void connectionLost(Throwable throwable) {

            }

            @Override
            public void messageArrived(String topic, MqttMessage mqttMessage) throws Exception {
                Log.w("Debug", mqttMessage.toString());
                
				//Assigns packet payload to data variable converted to a string
				data = mqttMessage.toString();

				//if the string has the "wl" key indicator then change the water label and update progress circle
                if(data.toLowerCase().contains("wl"))
                {
                    data = data.substring(2);
                    water.setText(("Current Water level ==> " +data+"%"));
                    pcircle.setProgress(Integer.parseInt(data));

                }

				//if the string contains "m" key indicator then change the condition label accordingly
                if (data.toLowerCase().contains("m"))
                {
                    //data = data.substring(1);
                    if (data.toLowerCase().contains("1"))
                    {
                        condition.setText(("Plant needs to be watered!"));
                    }

                    else
                    {
                        condition.setText(("Plant has been watered!"));
                    }

                }

            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken iMqttDeliveryToken) {

            }
        });
    }
}
