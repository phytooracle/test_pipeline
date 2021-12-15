import os
import pdb
import yaml
import numpy as np
import filesystem_functions
import pprint

__root_path__ = "."

def divide_list_into_chunks(a, n):
    """
    From https://stackoverflow.com/questions/2130016/
    a: list to be split
    n: number of chunks
    """
    k, m = divmod(len(a), n)
    return list((a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n)))

def comparison_row(plant_name, tags, color):

    return_html = ""
    return_html += f"""
    <tr>
    <td bgcolor={color}>
        <p style="color:white;">{plant_name}</p>
    </td>
    <td>
    """

    for tag in tags:

        return_html += f"""
        <table>
        <tr>
        <td>
            {"<br>".join(tag.split("_"))}
        </td>
        <td>
            <a href="{tag}/plant_reports/{plant_name}/level_1_plant_clip.gif"><img style="max-width: 300; max-height: 300px" src='{tag}/plant_reports/{plant_name}/level_1_plant_clip.gif'></a>
            <!input type="checkbox" name="crop" onchange="do_crop_checkbox()"/>
        </td>
        <td>
            <a href="{tag}/plant_reports/{plant_name}/soil_segmentation.gif"><img style="max-width: 300; max-height: 300px" src='{tag}/plant_reports/{plant_name}/soil_segmentation.gif'></a>
            <!input type="checkbox" name="ground" onchange="do_ground_checkbox()" />
        </td>
        <td>
            <a href="{tag}/plant_reports/{plant_name}/final.gif"><img style="max-width: 300; max-height: 300px" src='{tag}/plant_reports/{plant_name}/final.gif'></a>
            <!input type="checkbox" name="segmentation" onchange="do_segmentation_checkbox()" />
        </td>
        </tr>
        </table>
        """
    return_html += "</td></tr>"
    return return_html


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
        self.do_setup()

    def do_setup(self):
        pass

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


class OutputTagPage(GenericPage):

    def do_setup(self):
        self.import_yaml()
        self.date = self.name.split("/")[0]

    def header(self):
        foo = self.make_compare_with_links()
        return f"""
            <html>
            <head>
            <link href="https://fonts.googleapis.com/css?family=Montserrat" rel="stylesheet">
            <link href="https://codepen.io/chriddyp/pen/bWLwgP.css" rel="stylesheet">
            </head>
            <a href="../../../index.html">Dashboard Home</a><br>
            <h1>{self.name}</h1>
            <hr>
            <table>
            <tr>
            <td width="50%">
                <small>
                    <a href="../config.yaml">The YAML File!...</a><br>
                    <pre>{pprint.pformat(self.yaml_dict['tags'])}</pre>
                </small>
            </td>
            <td>
                <b>Compare this output with other {self.date} runs:</b><br>
                {foo}
            </td>
            </tr>
            </table>
        """

    def make_compare_with_links(self):
        import itertools
        return_html = ""

        # Get all combinations of tags
        tag_paths = filesystem_functions.get_tag_paths(self.date)
        date_tags = filesystem_functions.convert_paths_to_names(tag_paths)
        date_tags.sort()
        tag_combinations = list(itertools.combinations(date_tags, 2))

        # we only want combinations that have the current tag (self_tag) in them
        self_tag = self.name.split("/")[-2]
        for combination in tag_combinations:
            link_text = None
            combination_name = "-vs-".join(combination)
            if combination[0] == self_tag:
                link_text = f"vs {combination[1]}"
            if combination[1] == self_tag:
                link_text = f"vs {combination[0]}"
            #breakpoint()

            if link_text is not None:
                return_html += f"<li><a href='../../{combination_name}_1.html'>{link_text}</a>\n"

        return return_html
        

    def footer(self):
        return f"""
            <hr>
            <small>
            Full Yaml File:<p>
            <pre>{pprint.pformat(self.yaml_dict)}</pre>
            </small>
            </body>
            </html>
        """


    def import_yaml(self):

        with open(os.path.join(self.name,"config.yaml"), 'r') as stream:
            try:
                self.yaml_dict = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

