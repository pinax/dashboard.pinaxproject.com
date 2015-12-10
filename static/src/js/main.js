window.jQuery = window.$ = require("jquery");

require("bootstrap");

require("../less/site.less");

var Chart = require("chart.js");

$(function () {
    var ctx = document.getElementById("myChart").getContext("2d");
    $.ajax({
        url: $("#myChart").data("chart-data-url"),
        success: function (data) {
            var myNewChart = new Chart(ctx).Bar(data);
        }
    })
});
