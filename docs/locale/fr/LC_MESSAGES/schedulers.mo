��          �               L     M  �   R     �  .   �  �   %  �   �     F  
   M  
   X  #   c  	   �    �  D  �  �   �     �  �   �  &   o  p   �  l       t	  �   y	     $
  0   +
  �   \
  �   �
     �     �     �  4   �     �  �     o  �  �   i  -   `  �   �  +   Z  �   �   Date Even before trying to insert some bank transaction, a better approach would be to create first bank transaction schedulers (for recurring payments for e.g). Fields For the moment, there is two kinds of periods: Keep in mind that when the background task (cron) would try to clone a bank transaction, it will create it for the **next** date. On the page of the bank account, click on the link *Schedule* in the menu tab links. You are redirect on the scheduler overview page. On this page, you could: Period Recurrence Schedulers Some fields need more explanations: Start now The *date* is used to be repeated for the next corresponding period. For example, if you have a rent every 10 of the month, you should write a date where day is 10, and month is the **current** month (not the next month), even if the current day is 26 for example. When you create a scheduler, you may be interesting in running it immediatly. However be careful, it would create a new bank transaction for the **next** period based on the date/period given. Thus, if you want to create an automatic bank transaction for the current month, the date field must be set for the previous month. You can specify how many time the scheduler will be repeat with the *recurrence* field. Leave it empty to be repeated indefinitely. If not infinite, when 0 is reached, the scheduler is automatically deleted. add/edit/delete scheduler monthly: clone bank transactions every months for a given date. Don't worry, each month is properly respected : The 2015-01-29 will be 2015-02-28 for the next month. see a summary of periodic debit/credit weekly: clone bank transactions every weeks for a given date, depending on localization (i.e first day of week). Project-Id-Version: MyMoney 1.0
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2015-07-28 21:33+0200
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language-Team: fr <LL@li.org>
Plural-Forms: nplurals=2; plural=(n > 1)
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.0
 Date Avant même d'essayer de créer de nouvelles transactions, une meilleure approche serait de créer d'abord des planifications (pour des paiments récurrents par exemple). Champs Pour le moment, il y a deux types de périodes : Gardez à l'esprit que lorsque la tâche de fond (cron) essaye de dupliquer les transactions bancaires, ce sera pour la date **suivante**. Sur la page du compte bancaire, cliquez sur le lien *Planifier* de l'onglet du menu. Vous êtes redirigé sur la page d'aperçu des planifications. Sur cette page, vous pouvez : Période Récurrence Planifications Certains champs nécessitent quelques explications : Commencer maintenant La *date* est utilisée comme base pour les répétitions. Par exemple, si vous avez un loyer tous les 10 du mois, vous devriez saisir une date au 10 pour le mois courant (pas le mois suivant), même si le jour courant est le 26 par exemple. Quand vous créer une planification, vous serez peut-être intéressé pour la lancer immédiatement. Cependant prenez garde, cela va créer une nouvelle transaction bancaire pour la période **suivante** de la date donnée. Donc si vous voulez créer une transaction bancaire automatique pour le mois courant, le champ date doit être saisi avec le mois précédent. Vous pouvez spécifier combien de fois la planification sera répétée avec le champ *récurrence*. Laissez le vide pour une répétition infinie. Si elle n'est pas infinie, quand 0 est atteint, la planificiation sera automatiquement supprimée. ajouter/modifier/supprimer des planifications mensuelle : duplique les transactions bancaires tous les mois à partir d'une date. Pas d'inquiétude, chaque mois est correctement respecté : le 29/01/2015 deviendra le 28/02/2015 pour le mois suivant. voir un résumé périodique débit/crédit hebdomadaire : duplique les transactions bancaires toutes les semaines à partir d'une date, dépendant de la localisation (premier jour de la semaine). 