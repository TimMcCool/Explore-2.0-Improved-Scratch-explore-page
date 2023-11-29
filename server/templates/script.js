   
var limit = 16;
var offset = 0;
defaultTags = ["*", "all", "animations", "art", "games", "tutorials", "contests", "intros", "platformers", "pen"]
nonTitleTags = ["*", "all", "animations", "art", "games", "tutorials", "stories", "platformers", "intros", "contests", "pen"]

// Get current tag tab
site = window.location.href;
if (site.includes("explore/projects/")) {
    site = site.split('/')
    var tag = site[site.length - 2]
    tag = tag.replaceAll("%20", " ")
} else {
    var tag = "*"
}
if (location.search.includes("lang=")) {
    lang = location.search.split('lang=')[1].split("&")[0]
} else {
    lang = null
}
if (location.search.includes("mode=")) {
    mode = location.search.split('mode=')[1].split("&")[0]
} else {
    mode = "trending"
}
console.log(tag)

function getProjects(tag, limit=16, offset=0) {
    fetch('/api/'+tag+'/?limit='+limit.toString()+"&offset="+offset.toString()+"&lang="+lang+"&mode="+mode)
       .then((response) => response.json())
       .then((response) => addProjects(response))
}

function addProjects(projects) {
    for (const project of projects) {
        insertProject(project);
    }
    document.getElementById("more").innerHTML = "Load more"
    console.log(projects)
    if (projects.length == 0) {
        element = document.getElementById("more")
        
        if (nonTitleTags.includes(tag)) {
            element.parentElement.innerHTML = element.parentElement.innerHTML + '<p class="notification">This page is being calculated right now</p>'
        } else {
            element.parentElement.innerHTML = element.parentElement.innerHTML + '<p class="notification">That was all!</p>'
        }
        document.getElementById("more").remove();
    }
}

function insertProject(project) {
    const grid = document.getElementById("projectGrid");
    console.log(grid);
    //project_div = '<div class="thumbnail project"><a class="thumbnail-image" href="/projects/'+project["id"].toString()+'/"><img alt="" src="https://cdn2.scratch.mit.edu/get_image/project/'+project["id"].toString()+'_480x360.png"></a><div class="thumbnail-info"><a class="creator-image" href="/users/'+project["author"].toString()+'/"><img alt="'+project["author"].toString()+'" src="https://cdn2.scratch.mit.edu/get_image/user/72092169_32x32.png"></a><div class="thumbnail-title"><a href="/projects/'+project["id"].toString()+'/" title="'+project["title"]+'">'+project["title"].toString()+'</a><div class="thumbnail-creator"><a href="/users/'+project["author"].toString()+'/">'+project["author"].toString()+'</a></div></div></div></div>'
    project_div = '<div class="thumbnail project"><a class="thumbnail-image" target="_blank" href="https://scratch.mit.edu/projects/'+project["id"].toString()+'/"><img alt="" src="https://cdn2.scratch.mit.edu/get_image/project/'+project["id"].toString()+'_480x360.png"></a><div class="thumbnail-info"><a class="creator-image" href="/users/'+project["author"].toString()+'/"><div class="thumbnail-title"><a target="_blank" href="https://scratch.mit.edu/projects/'+project["id"].toString()+'/" title="'+project["title"]+'">'+project["title"].toString()+'</a><div class="thumbnail-creator"><a target="_blank" href="https://scratch.mit.edu/users/'+project["author"].toString()+'/">'+project["author"].toString()+'</a></div></div></div></div>'
    grid.innerHTML = grid.innerHTML + project_div
}


function loadMore() {
    document.getElementById("more").innerHTML = "Loading ..."
    offset += 16;
    getProjects(tag, limit=limit, offset=offset);
}

window.onload = function init() {
    if (mode=="popular") {
        offset -=16;
        loadMore()
    }
    if (!nonTitleTags.includes(tag)) {
        const grid = document.getElementById("projectBox");
        grid.innerHTML = "<p class='notification'>Only titles are checked for this tag</p>" + grid.innerHTML
    }
    if (!defaultTags.includes(tag)) {
        tag_div = '<a href="/explore/projects/'+tag+'/"><li class="active"><span>'+tag+'</span></li></a>'
        document.getElementsByClassName("sub-nav categories")[0].innerHTML += tag_div
    }
}
