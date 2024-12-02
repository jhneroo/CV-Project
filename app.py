from flask import (
    Flask, render_template, request, redirect, url_for, session, jsonify)
from tensorflow import keras
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
import io
import base64
import matplotlib 
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# def get_conv_layers_and_weights(layer, conv_layers, model_weights):
#     if isinstance(layer, layers.Conv2D):
#         model_weights.append(layer.get_weights())
#         conv_layers.append(layer)
#     elif hasattr(layer, 'layers'):
#         for sub_layer in layer.layers:
#             get_conv_layers_and_weights(sub_layer, conv_layers, model_weights)

def get_layers(layer, layers_list, weights_list, names_list):
    if isinstance(layer, layers.Conv2D):
        layers_list.append(layer)
        weights_list.append(layer.get_weights())
        names_list.append(f"Conv2D_{layer.name}")
    elif isinstance(layer, layers.MaxPooling2D):
        layers_list.append(layer)
        names_list.append(f"MaxPool_{layer.name}")
    elif isinstance (layer, layers.Dropout):
        layers_list.append(layer)
        names_list.append(f"Dropout_{layer.name}")
    elif isinstance (layer, layers.Dense):
        layers_list.append(layer)
        names_list.append(f"Dense_{layer.name}")
    elif hasattr(layer, 'layers'):
        for sub_layer in layer.layers:
            get_layers(sub_layer, layers_list, weights_list, names_list)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/recognize', methods=['GET'])
def recognize_get():
    print('in recognize get')
    return render_template('recognize.html')


@app.route('/recognize', methods=['POST'])
def recognize_post():
    pixels = request.form['pixels']
    pixels = pixels.split(',')
    image = np.array(pixels).astype(float).reshape(1, 50, 50, 1)
    
    model = keras.models.load_model('numbers4.keras')
    pred = np.argmax(model.predict(image), axis=-1)
    print(f"Prediction Value: {pred[0]}")

    conv_layers = []
    model_weights = []
    layers_list = []
    weights_list = []
    names_list = []

    for layer in model.layers:
        get_layers(layer, layers_list, weights_list, names_list)
        # get_conv_layers_and_weights(layer, conv_layers, model_weights)

    current_output = image

    outputs = []
    labels = []

    # for layer in conv_layers:
    #     image = layer(image)
    #     outputs.append(image)
    #     names.append(str(layer))

    # Process each layer and collect outputs
    for i, layer in enumerate(layers_list):
        if isinstance (layer, (layers. Conv2D, layers.MaxPooling2D, layers.Dropout)):
            # Process the current layer with the previous layer's output
            current_output = layer(current_output, training=False) # Set training=False for consistent results
            outputs.append(current_output)
            labels.append(names_list[i])
        elif isinstance(layer, layers. Flatten):
            current_output = layer(current_output)
            outputs.append(current_output)
            labels.append("Flatten")

    # processed = []
    # for feature_map in outputs:
    #     feature_map = tf.squeeze(feature_map, axis=0)
    #     num_filters = feature_map.shape[-1]

    #     for j in range(num_filters):
    #         single_filter_map = feature_map[:, :, j].numpy()
    #         processed.append(single_filter_map)

    

    # processed_images = []
    # for i, fm in enumerate(processed):
    #     fig, ax = plt.subplots(figsize=(4, 4))
    #     ax.imshow(fm, cmap="viridis")
    #     ax.axis("off")
    #     ax.set_title(f'Feature Map {i}', fontsize=10)

    #     buf = io.BytesIO()
    #     fig.savefig(buf, format='png', bbox_inches='tight')
    #     plt.close(fig)
    #     buf.seek(0)

    #     img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    #     processed_images.append(img_base64)

    processed_images = []

    for i, feature_map in enumerate(outputs):
        if len(feature_map.shape) == 2: # Flattened output
            single_filter_map = feature_map.numpy()
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.bar(np.arange(len(single_filter_map[0])), single_filter_map[0])
            ax.set_xlabel('Index')
            ax.set_ylabel('Value')
            ax.set_title(f'{labels[i]} - Flattened layer')
        
        else:
            feature_map = tf.squeeze(feature_map, axis=0)
            num_filters = feature_map.shape[-1]

            grid_size = int(np.ceil(np.sqrt(num_filters)))
            fig, axes = plt.subplots(grid_size, grid_size, figsize=(12, 12))

            if num_filters == 1:
                axes = np.array([[axes]])
            elif grid_size == 1:
                axes = np.array([axes])

            for filter_idx in range(num_filters):
                row = filter_idx // grid_size
                col = filter_idx % grid_size
                single_filter_map = feature_map[:, :, filter_idx].numpy()
                axes[row, col].imshow(single_filter_map, cmap='viridis')
                axes[row, col].axis('off')

            for j in range(num_filters, grid_size * grid_size):
                row = j // grid_size
                col = j % grid_size
                axes[row, col].axis('off')

            plt.suptitle(f'{labels[i]} - Feature Maps')

        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)

        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        processed_images.append(img_base64)


    return jsonify(pred=pred[0].item(), images=processed_images)

if __name__ == '__main__':
    app.run(debug=True)
