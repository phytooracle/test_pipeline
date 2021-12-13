import os
import pdb
import numpy as np

__root_path__ = "."

def plant_data_row(plant_name):

    return f"""
    <tr>
    <td>
        <a href="{plant_name}/">{plant_name}</a><br>
    </td>
    <td>
        <a href="{plant_name}/level_1_plant_clip.gif"><img style="max-width: 300; max-height: 300px" src='{plant_name}/level_1_plant_clip.gif'></a>
    </td>
    <td>
        <a href="{plant_name}/soil_segmentation.gif"><img style="max-width: 300; max-height: 300px" src='{plant_name}/soil_segmentation.gif'></a>
    </td>
    <td>
        <a href="{plant_name}/final.gif"><img style="max-width: 300; max-height: 300px" src='{plant_name}/final.gif'></a>
    </td>
    <td>
        <a href="{plant_name}/poly_crop-fitting.jpg"><img style="max-width: 300; max-height: 300px" src='{plant_name}/poly_crop-fitting.jpg'></a>
    </td>
    """


def create_random_plants_page(plants, conf, n=50, filename="random.html"):

    html = f"""
        <html>
        <body>
        <h1>{n} Random Valid Plants : {conf.args.date}</h1>
        <table>

        <tr><th></th><th></th><th>Geocorection<th>Soil<br>Identification</th><th>Plant<br>Segmentation</th></tr>
    """

    if len(plants) < n:
        n = len(plants)

    # Because random.choice doesn't like multidimensional things,
    # we have to do it this way...
    indices = np.random.choice(len(plants), n, replace=False)
    for i in indices:
        plant_data = plants[i]
        html += plant_data_row(plant_data, conf.BASE_URL, conf)

    html += """
        </tr>
        <tr>
            <td></td>
            <td></td>
            <td><center><label id="cropCount">Flagged: 0</label></center></td>
            <td><center><label id="groundCount">Flagged: 0</label></center></td>
            <td><center><label id="segmentationCount">Flagged: 0</label></center></td>
        </tr>
        </table>
<p>
		<script>
			function do_crop_checkbox() {
			  let total = document.querySelectorAll('input[name="crop"]:checked').length;
			  let perc = total / document.querySelectorAll('input[name="crop"]').length * 100;
			  document.getElementById("cropCount").innerHTML = "Flags: " + total + " (" + perc.toFixed(2) + "%)";
			}
			function do_ground_checkbox() {
			  let total = document.querySelectorAll('input[name="ground"]:checked').length;
			  let perc = total / document.querySelectorAll('input[name="ground"]').length * 100;
			  document.getElementById("groundCount").innerHTML = "Flags: " + total + " (" + perc.toFixed(2) + "%)";
			}
			function do_segmentation_checkbox() {
			  let total = document.querySelectorAll('input[name="segmentation"]:checked').length;
			  let perc = total / document.querySelectorAll('input[name="segmentation"]').length * 100;
			  document.getElementById("segmentationCount").innerHTML = "Flags: " + total + " (" + perc.toFixed(2) + "%)";
			}
		</script>
<p>
		<hr>
		<p><a href="index.html">Scan Home</a></p>
        <br>
        <hr>
        <p>
		</body>
        </html>
    """

    with open(filename, "w") as html_file:
        html_file.write(html);


class GenericPage(object):

    def __init__(self, save_path):
        self.save_path = save_path
        self.html_body = "<body>\n"

    def footer(self):
        return """
            </body>
            </html>
        """

    def header(self):
        return """
            <html>
            <head>
            <link href="https://fonts.googleapis.com/css?family=Montserrat" rel="stylesheet">
            <link href="https://codepen.io/chriddyp/pen/bWLwgP.css" rel="stylesheet">
            </head>
        """

    def assemble_output(self):
        output = ""
        output += self.header()
        output += self.html_body
        output += self.footer()
        return output

    def __iadd__(self, html_to_add):
        self.html_body += html_to_add
        return self

    #def __del__(self):
        #pass

    def save_page(self):
        with open(os.path.join(__root_path__, self.save_path), "w") as output_file:
            output_file.write(self.assemble_output());
