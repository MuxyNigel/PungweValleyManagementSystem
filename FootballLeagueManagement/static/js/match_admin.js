(function($) {
    $(document).ready(function() {
        var homeTeamField = $('#id_home_team');
        var awayTeamField = $('#id_away_team');
        var homeScoreField = $('#id_home_team_score');
        var awayScoreField = $('#id_away_team_score');

        var homePlayers = [];
        var awayPlayers = [];
        var homeTeamName = "Home Team";
        var awayTeamName = "Away Team";

        function updatePlayerDropdowns() {
            var goalRows = $('.dynamic-goals');
            
            goalRows.each(function(index, row) {
                var scorerSelect = $(row).find('select[name$="-scorer"]');
                var assistSelect = $(row).find('select[name$="-assist"]');
                
                // Do not update the empty-form template row directly if we can avoid it, but we need to so new rows have it
                // Actually, formset:added handles new rows, but updating the empty-form is good too.
                
                if (scorerSelect.length > 0) {
                    var currentScorer = scorerSelect.val();
                    var currentAssist = assistSelect.val();
                    
                    var optionsHtml = '<option value="">---------</option>';
                    
                    if (homePlayers.length > 0) {
                        optionsHtml += '<optgroup label="' + homeTeamName + '">';
                        homePlayers.forEach(function(p) {
                            optionsHtml += '<option value="' + p.id + '">' + p.name + '</option>';
                        });
                        optionsHtml += '</optgroup>';
                    }
                    
                    if (awayPlayers.length > 0) {
                        optionsHtml += '<optgroup label="' + awayTeamName + '">';
                        awayPlayers.forEach(function(p) {
                            optionsHtml += '<option value="' + p.id + '">' + p.name + '</option>';
                        });
                        optionsHtml += '</optgroup>';
                    }
                    
                    scorerSelect.html(optionsHtml);
                    scorerSelect.val(currentScorer);
                    
                    assistSelect.html(optionsHtml);
                    assistSelect.val(currentAssist);
                }
            });
        }

        function fetchPlayers() {
            var homeTeamId = homeTeamField.val();
            var awayTeamId = awayTeamField.val();
            
            if (homeTeamId) homeTeamName = homeTeamField.find('option:selected').text();
            if (awayTeamId) awayTeamName = awayTeamField.find('option:selected').text();

            if (homeTeamId || awayTeamId) {
                $.ajax({
                    url: '/api/admin-match-players/',
                    data: {
                        'home_team_id': homeTeamId || '',
                        'away_team_id': awayTeamId || ''
                    },
                    success: function(data) {
                        homePlayers = data.home_players;
                        awayPlayers = data.away_players;
                        updatePlayerDropdowns();
                    }
                });
            } else {
                homePlayers = [];
                awayPlayers = [];
                updatePlayerDropdowns();
            }
        }

        function syncGoalRows() {
            var hScore = parseInt(homeScoreField.val()) || 0;
            var aScore = parseInt(awayScoreField.val()) || 0;
            var totalGoals = hScore + aScore;
            
            setTimeout(function() {
                var visibleRows = $('.dynamic-goals').not('.empty-form').filter(function() {
                    // check if they are marked for deletion
                    var isDeleted = $(this).find('input[name$="-DELETE"]').is(':checked');
                    return !isDeleted;
                }).length;
                
                var addRowButton = $('#goals-group .add-row a');
                
                if (totalGoals > visibleRows && addRowButton.length > 0) {
                    for (var i = visibleRows; i < totalGoals; i++) {
                        addRowButton.click();
                    }
                }
            }, 100);
        }

        homeTeamField.change(fetchPlayers);
        awayTeamField.change(fetchPlayers);
        homeScoreField.change(syncGoalRows);
        awayScoreField.change(syncGoalRows);

        // Initial fetch
        fetchPlayers();
        // Initial sync
        // syncGoalRows(); // We probably shouldn't auto-add rows on initial load, only on change.

        // Update dropdowns when a new row is added
        $(document).on('formset:added', function(event, $row, formsetName) {
            if (formsetName === 'goals') {
                updatePlayerDropdowns();
            }
        });
        
        // Highlight own goals
        $(document).on('change', 'input[name$="-is_own_goal"]', function() {
            var row = $(this).closest('.dynamic-goals');
            if ($(this).is(':checked')) {
                row.css('background-color', '#ffe6e6');
            } else {
                row.css('background-color', '');
            }
        });
        
        $('input[name$="-is_own_goal"]:checked').closest('.dynamic-goals').css('background-color', '#ffe6e6');
    });
})(django.jQuery);
