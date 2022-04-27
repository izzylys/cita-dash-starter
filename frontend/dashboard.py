import operator
from functools import reduce

import pandas as pd
from PIL import Image
import streamlit as st
import plotly.express as px
from specklepy.api import operations
from specklepy.api.wrapper import StreamWrapper

from utils import (
    send_notes,
    list_to_md,
    format_commit,
    format_branch,
    simplify_glulam,
    preview_from_commit,
    preview_from_object,
    create_print_data_df,
)

# --------------------------
# PAGE CONFIG
favicon = Image.open("frontend/assets/speckle-chart-logo.png")

st.set_page_config(page_title="Dashboard", page_icon=favicon)

header = st.container()
user_input = st.container()
viewer = st.container()
glulam_analysis = st.container()
print_analysis = st.container()
stream_stats = st.container()
stream_stats_graphs = st.container()
# --------------------------

# --------------------------
# HEADER
# Page Header
with header:
    st.title("Demo Dashboard")
# About info
with header.expander("Links & More 🔽", expanded=True):
    st.markdown(
        """
        A sample dashboard to get you started! This dashboard is written entirely in python using streamlit which make it easy to get something onto a webpage asap.

        💫 Want to to take it a step further? Have a look at this [Revit Carbon Calculator](https://github.com/specklesystems/SpeckleHackathon-SpeckleReports/tree/connect/py-workshop) which automates calculations using webhooks handled by a FastAPI server and a python frontend built with Plotly / Dash

        🕸 Curious about webhooks? Have a look at [this tutorial](https://speckle.systems/tutorials/webhooks-discord-tutorial/) to learn more about how they work and how you could use them
        
        📖 Head to [speckle.guide](https://speckle.guide/dev/python.html) for `specklepy` documentation

        📺 Check out the [Speckle Streamlit tutorial](https://speckle.systems/tutorials/create-your-first-speckle-app-using-only-python/) by Bilal for more on building the stream statistics portion of this dashboard. Big thanks to Bilal for letting me borrow some of his tut for this demo!
        """
    )
# --------------------------

# --------------------------
# INPUTS
with user_input:
    st.subheader("Inputs")
    # User Input boxes
    input_url = st.text_input(
        "Stream URL",
        "https://speckle.xyz/streams/2c010399e5/",
        help="Paste in the URL of the stream",
    )
    speckleToken = st.text_input(
        "Speckle token",
        "",
        help="If you're not sure where how to get a token, take a look at this [link](https://speckle.guide/dev/tokens.html)👈. If you're running this app locally with local accounts present, you won't need to input your token.",
    )

    # CLIENT
    wrapper = StreamWrapper(input_url)
    client = wrapper.get_client(speckleToken)

    # SELECTED STREAM ✅
    stream = client.stream.get(wrapper.stream_id, 15, commit_limit=20)

    branch_input_col, commit_input_col = st.columns(2)

    branches = stream.branches.items
    selected_branch = branch_input_col.selectbox(
        "Branch", branches, format_func=format_branch
    )
    commits = selected_branch.commits.items

    selected_commit = commit_input_col.selectbox(
        "Commit", commits, format_func=format_commit
    )

# --------------------------
# VIEWER
if selected_commit:
    with viewer:
        st.subheader("Selected Commit 👇")
        st.write(
            f"Open this commit in [the frontend]({wrapper.server_url}/streams/{wrapper.stream_id}/commits/{selected_commit.id}) 🚀"
        )
        preview_from_commit(wrapper, selected_commit)
# --------------------------

# --------------------------
# Glulam Analysis
commit_obj = (
    operations.receive(
        selected_commit.referencedObject, wrapper.get_transport(speckleToken)
    )
    if selected_commit
    else None
)

if glulams := getattr(commit_obj, "@glulams", []):
    glulam_df = pd.DataFrame.from_dict([simplify_glulam(g) for g in glulams])
    with glulam_analysis:
        st.subheader("🧴🐑 Analysis")

        st.dataframe(glulam_df)
        mesh_df = pd.DataFrame(None, columns=["x", "y", "z", "id"])
        notes = {}
        with st.form("glulam_notes", clear_on_submit=False):
            for g in glulams:
                with st.expander(f"Glulam {g.id}"):
                    data_col, preview_col = st.columns(2)
                    data_col.json(simplify_glulam(g))
                    with preview_col:
                        preview_from_object(wrapper, g.id, height=250)
                    verts_list = g["@glulam"]["@displayValue"][0]["vertices"]
                    verts = [
                        verts_list[i : i + 3] for i in range(0, len(verts_list), 3)
                    ]
                    verts_df = pd.DataFrame(verts, columns=["x", "y", "z"])
                    verts_df["id"] = g.id
                    mesh_df = pd.concat([mesh_df, verts_df])
                    fig = px.scatter(verts_df, x="y", y="z")
                    fig.update_layout(height=350)
                    fig.update_yaxes(
                        scaleanchor="x",
                        scaleratio=1,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    notes[g.id] = st.text_area(
                        "Add a note",
                        value=getattr(g, "note", ""),
                        key=g.id,
                        max_chars=500,
                    )
            if submit := st.form_submit_button("Send Notes"):
                has_changed = False
                for g in glulams:
                    if g.id in notes and notes[g.id] != getattr(g, "note", ""):
                        has_changed = True
                        g.note = notes[g.id]

                if has_changed:
                    commit_id = send_notes(
                        wrapper, glulams, branch_name="glulam-updates"
                    )
                    st.write(f"Commit created ({commit_id})")

                has_changed = False
# --------------------------

# --------------------------
# 3D Print Path Analysis
print_path_df = create_print_data_df(commit_obj) if commit_obj else None
if print_path_df is not None and not print_path_df.empty:
    with print_analysis:
        st.subheader("🦾 3D Print Analysis")

        fig_speed_delta_and_dev = px.line(
            print_path_df,
            x="time",
            y=["deviation", "speedDelta", "speed"],
            title="Deviation, Speed, and Speed Delta Over Time",
        )
        st.plotly_chart(fig_speed_delta_and_dev, use_container_width=True)

        fig_speed_delta = px.line(
            print_path_df, x="time", y="speedDelta", title="Speed Delta Over Time"
        )
        st.plotly_chart(fig_speed_delta, use_container_width=True)

        fig_speed_dev = px.scatter(
            print_path_df,
            x="time",
            y="deviation",
            color="speed",
            title="Deviation Over Time Coloured By Speed",
        )
        st.plotly_chart(fig_speed_dev, use_container_width=True)

        fig_location_by_dev = px.scatter_3d(
            print_path_df,
            x="x",
            y="y",
            z="z",
            color="deviation",
            opacity=0.7,
            title="Print Path Coloured By Deviation",
        )
        fig_location_by_dev.update_traces(marker_size=4)
        fig_location_by_dev.update_layout(
            scene=dict(
                zaxis=dict(
                    nticks=4,
                    range=[-0.5, 0.75],
                ),
            ),
        )
        st.plotly_chart(fig_location_by_dev, use_container_width=True)

        fig_location_by_speed = px.scatter_3d(
            print_path_df,
            x="x",
            y="y",
            z="z",
            color="speed",
            opacity=0.7,
            title="Print Path Coloured By Speed",
        )
        fig_location_by_speed.update_traces(marker_size=4)
        fig_location_by_speed.update_layout(
            scene=dict(
                zaxis=dict(
                    nticks=4,
                    range=[-0.5, 0.75],
                ),
            ),
        )
        st.plotly_chart(fig_location_by_speed, use_container_width=True)
# --------------------------

# --------------------------
# STREAM STATISTICS
with stream_stats:
    st.subheader("Stream Statistics")

    # -------
    # Columns for Cards
    branchCol, commitCol, connectorCol, contributorCol = st.columns(4)
    # -------

    # -------
    # Branch Card 💳
    branchCol.metric(label="Number of branches", value=stream.branches.totalCount)
    # branch names as markdown list
    branchNames = [b.name for b in branches]
    list_to_md(branchNames, branchCol)
    # -------

    # -------
    # Commit Card 💳
    commitCol.metric(label="Number of commits", value=len(commits))
    # -------

    # -------
    # Connector Card 💳
    # connector list
    connectorList = [c.sourceApplication for c in commits]
    # number of connectors
    connectorCol.metric(
        label="Number of connectors", value=len(dict.fromkeys(connectorList))
    )
    # get connector names
    connectorNames = list(dict.fromkeys(connectorList))
    # convert it to markdown list
    list_to_md(connectorNames, connectorCol)
    # -------

    # -------
    # Contributor Card 💳
    contributorCol.metric(
        label="Number of contributors", value=len(stream.collaborators)
    )
    # unique contributor names
    contributorNames = {col.name for col in stream.collaborators}
    # convert it to markdown list
    list_to_md(contributorNames, contributorCol)
    # -------
# --------------------------

# --------------------------
# STREAM GRAPHS
with stream_stats_graphs:
    st.subheader("Graphs")
    # COLUMNS FOR CHARTS
    connector_graph_col, collaborator_graph_col = st.columns(2)

    # -------
    # CONNECTOR CHART 🍩
    commits = [b.commits.items for b in stream.branches.items]
    commits = reduce(operator.concat, commits)
    commits = pd.DataFrame.from_dict([c.dict() for c in commits])
    # get apps from commits
    apps = commits["sourceApplication"]
    # reset index
    apps = apps.value_counts().reset_index()
    # rename columns
    apps.columns = ["app", "count"]
    # donut chart
    fig = px.pie(apps, names="app", values="count", hole=0.4)
    # set dimensions of the chart
    fig.update_layout(
        showlegend=True,
        height=350,
        yaxis_scaleanchor="x",
        title="Commits by Source Application",
    )
    # set width of the chart so it uses column width
    connector_graph_col.plotly_chart(fig, use_container_width=True)
    # -------

    # -------
    # COLLABORATOR CHART 🍩
    # get authors from commits
    authors = commits["authorName"].value_counts().reset_index()
    # rename columns
    authors.columns = ["author", "count"]
    # create our chart
    authorFig = px.pie(authors, names="author", values="count", hole=0.4)
    authorFig.update_layout(
        showlegend=True, height=350, yaxis_scaleanchor="x", title="Commits by Author"
    )
    collaborator_graph_col.plotly_chart(authorFig, use_container_width=True)
    # -------

    # -------
    # BRANCH GRAPH 📊
    # branch count dataframe
    branch_counts = pd.DataFrame(
        [[branch.name, branch.commits.totalCount] for branch in branches]
    )
    # rename dataframe columns
    branch_counts.columns = ["branchName", "totalCommits"]
    # create graph
    branch_count_graph = px.bar(
        branch_counts,
        x=branch_counts.branchName,
        y=branch_counts.totalCommits,
        color=branch_counts.branchName,
        labels={"branchName": "", "totalCommits": ""},
    )
    # update layout
    branch_count_graph.update_layout(
        showlegend=False, margin=dict(l=1, r=1, t=1, b=1), height=220
    )
    # show graph
    st.plotly_chart(branch_count_graph, use_container_width=True)
    # -------

    # -------
    # COMMIT PANDAS TABLE �
    st.subheader("Commit Activity Timeline 🕒")
    # created at parameter to dataframe with counts
    cdate = (
        pd.to_datetime(commits["createdAt"])
        .dt.date.value_counts()
        .reset_index()
        .sort_values("index")
    )
    # date range to fill null dates.
    null_days = pd.date_range(start=cdate["index"].min(), end=cdate["index"].max())
    # add null days to table
    cdate = cdate.set_index("index").reindex(null_days, fill_value=0)
    # reset index
    cdate = cdate.reset_index()
    # rename columns
    cdate.columns = ["date", "count"]
    # redate indexed dates
    cdate["date"] = pd.to_datetime(cdate["date"]).dt.date
    # -------

    # -------
    # COMMIT ACTIVITY LINE CHART📈
    # line chart
    fig = px.line(cdate, x=cdate["date"], y=cdate["count"], markers=True)

    # Show Chart
    st.plotly_chart(fig, use_container_width=True)
    # -------
# --------------------------
