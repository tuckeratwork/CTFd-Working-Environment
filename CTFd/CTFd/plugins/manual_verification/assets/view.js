window.challenge.data = undefined;

window.challenge.renderer = new markdownit({
  html: true,
  linkify: true
});

window.challenge.preRender = function() {};

window.challenge.render = function(markdown) {
  return window.challenge.renderer.render(markdown);
};

window.challenge.postRender = function() {
  // Don't hijack the enter button
  $("#submission-input").unbind("keyup");

  var submission_template =
    '<div class="card bg-light mb-4">\
    <div class="card-body">\
        <blockquote class="blockquote mb-0">\
            <p>{0}</p>\
            <small class="text-muted">{1}</small>\
        </blockquote>\
    </div>\
  </div>';

  $(".nav-tabs a").click(function(e) {
    if ($(e.target).attr("href") === "#submissions") {
      // Populate Submissions
      var challenge_id = parseInt($("#challenge-id").val());
      var url = "/submissions/" + challenge_id;

      CTFd.fetch(url, {
        method: "GET",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        }
      })
        .then(function(response) {
          return response.json();
        })
        .then(function(response) {
          var correct = response["data"]["correct"];
          var pending = response["data"]["pending"];

          $("#challenge-submissions").empty();
          $("#challenge-submissions").append($("<br>"));
          $("#challenge-submissions").append($("<h3>Correct</h3>"));
          for (var index = 0; index < correct.length; index++) {
            var s = correct[index];
            var entry = $(
              submission_template.format(
                htmlentities(s.provided),
                moment(s.date).fromNow()
              )
            );
            $("#challenge-submissions").append(entry);
          }

          $("#challenge-submissions").append($("<br>"));
          $("#challenge-submissions").append($("<hr>"));
          $("#challenge-submissions").append($("<br>"));

          $("#challenge-submissions").append($("<h3>Pending</h3>"));
          for (var index = 0; index < pending.length; index++) {
            var s = pending[index];
            var entry = $(
              submission_template.format(
                htmlentities(s.provided),
                moment(s.date).fromNow()
              )
            );
            $("#challenge-submissions").append(entry);
          }
        });
    }
    $(this).tab("show");
  });
};

window.challenge.submit = function(cb, preview) {
  var challenge_id = parseInt($("#challenge-id").val());
  var submission = $("#submission-input").val();
  var url = "/api/v1/challenges/attempt";

  if (preview) {
    url += "?preview=true";
  }

  var params = {
    challenge_id: challenge_id,
    submission: submission
  };

  CTFd.fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(params)
  })
    .then(function(response) {
      if (response.status === 429) {
        // User was ratelimited but process response
        return response.json();
      }
      if (response.status === 403) {
        // User is not logged in or CTF is paused.
        return response.json();
      }
      return response.json();
    })
    .then(function(response) {
      response.data.status = "already_solved";
      cb(response);
    });
};
