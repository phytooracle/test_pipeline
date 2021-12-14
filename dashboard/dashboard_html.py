import os
import pdb
import numpy as np

__root_path__ = "."

def divide_list_into_chunks(a, n):
    """
    From https://stackoverflow.com/questions/2130016/
    a: list to be split
    n: number of chunks
    """
    k, m = divmod(len(a), n)
    return list((a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n)))


def plant_data_row(plant_name):

    return f"""
    <tr>
    <td>
        <a href="{plant_name}/">{plant_name}</a><br>
    </td>
    <td>
        <a href="{plant_name}/level_1_plant_clip.gif"><img style="max-width: 300; max-height: 300px" src='{plant_name}/level_1_plant_clip.gif'></a>
        <input type="checkbox" name="crop" onchange="do_crop_checkbox()"/>
    </td>
    <td>
        <a href="{plant_name}/soil_segmentation.gif"><img style="max-width: 300; max-height: 300px" src='{plant_name}/soil_segmentation.gif'></a>
        <input type="checkbox" name="ground" onchange="do_ground_checkbox()" />
    </td>
    <td>
        <a href="{plant_name}/final.gif"><img style="max-width: 300; max-height: 300px" src='{plant_name}/final.gif'></a>
        <input type="checkbox" name="segmentation" onchange="do_segmentation_checkbox()" />
    </td>
    <td>
        <a href="{plant_name}/poly_crop-fitting.jpg"><img style="max-width: 300; max-height: 300px" src='{plant_name}/poly_crop-fitting.jpg'></a>
    </td>
    """

def plant_data_row_bottom():
    return """
        <tr>
            <td></td>
            <td><center><label id="cropCount">Flagged: 0</label></center></td>
            <td><center><label id="groundCount">Flagged: 0</label></center></td>
            <td><center><label id="segmentationCount">Flagged: 0</label></center></td>
            <td></td>
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
    """

    with open(filename, "w") as html_file:
        html_file.write(html);


class GenericPage(object):

    def __init__(self, save_path, name="Un-named"):
        self.path = self.save_path = save_path
        self.html_body = "<body>\n"
        self.name = name

    def footer(self):
        return """
            </body>
            </html>
        """

    def header(self):
        return f"""
            <html>
            <head>
            <link href="https://fonts.googleapis.com/css?family=Montserrat" rel="stylesheet">
            <link href="https://codepen.io/chriddyp/pen/bWLwgP.css" rel="stylesheet">
            </head>
            <h1>{self.name}</h1>
        """

    def add_link(self, page):
        self.html_body += f"<li><a href={page.path}>{page.name}</a>\n"

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
        output_path = os.path.join(__root_path__, self.save_path)
        print(f"Saving HTML: {output_path}")
        with open(output_path, "w") as output_file:
            output_file.write(self.assemble_output());
