# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PseudoCleaner
                                 A QGIS plugin
 PseudoCleaner
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-05-29
        git sha              : $Format:%H$
        copyright            : (C) 2019 by HanwGeek
        email                : HanwGeek@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtCore import QThread, QTime, QModelIndex, pyqtSignal
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QAction, QAbstractItemView
from qgis.core import QgsVectorLayer, QgsProject, QgsFeature, QgsGeometry, QgsFeatureRequest, QgsWkbTypes
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .Pseudo_Cleaner_dialog import PseudoCleanerDialog
from .Pseudo_Cleaner_result_view import PseudoCleanerTableView
from collections import defaultdict
import os.path

_DEBUG = True
class PseudoCleaner:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PseudoCleaner_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&PseudoCleaner')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PseudoCleaner', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Pseudo_Cleaner/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Pseudo Cleaner'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&PseudoCleaner'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False

            # init dialog
            self.dlg = PseudoCleanerDialog()
          
            # init tableview params
            self.resDlg = PseudoCleanerTableView()
            self.model = QStandardItemModel()
            self.model.setHorizontalHeaderLabels(["Point_X", "Point_Y", "Feature ID"])
            self.resDlg.mResTableView.verticalHeader().hide()
            self.resDlg.mResTableView.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.resDlg.mResTableView.setSelectionMode(QAbstractItemView.SingleSelection)
            self.resDlg.mResTableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.resDlg.mResTableView.clicked.connect(self._zoom_to_feature)

        # Loading layers for selection & init params
        self.canvas = self.iface.mapCanvas()
        self.corrSet = set()
        self.errSet = set()
        self.errFeatMap = defaultdict(list)
        self.errPointList = []
        self.dlg.mLayerComboBox.clear()

        layers = list(QgsProject.instance().mapLayers().values())
        for layer in layers:
          if layer.type() == layer.VectorLayer:
            self.dlg.mLayerComboBox.addItem(layer.name())

        # Start the work thread
        # self.workthread = WorkThread(iface=self.iface)
        # self.workthread.trigger.connect(self.dlg.pBar.setValue)
        # self.workthread.start()
        
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop

        result = self.dlg.exec_()
        
        # if OK to process the layer selected
        if result:
          self.lineLayer = layers[self.dlg.mLayerComboBox.currentIndex()]
          lineFeatIter = self.lineLayer.getFeatures()

          # Find pseudo points
          list(map(self._map_points_to_feat, lineFeatIter))

          # Init pseudo point data layer
          self._render_err_layer()
          # Add pseudo point data item to tableview 
          self._render_table()

          # show the reult table view dialog & errLayer
          QgsProject.instance().addMapLayer(self.errLayer)

          self.resDlg.show()

          res = self.resDlg.exec_() 
          if res:
            self._pseudo_clean()

          self.model.clear()

    def _map_points_to_feat(self, feat):
      g = feat.geometry()
      
      # Map features as point to id
      if g.isMultipart():
        lines = g.asMultiPolyline()
        for line in lines:
          startPoint, endPoint = line[0], line[-1]
          self.errFeatMap[startPoint].append(feat.id())
          self.errFeatMap[endPoint].append(feat.id())
      else:
        line = g.asPolyline()
        startPoint, endPoint = line[0], line[-1]
        self.errFeatMap[startPoint].append(feat.id())
        self.errFeatMap[endPoint].append(feat.id())

    def _pseudo_clean(self):
      # Union find feature set
      featCount = self.lineLayer.featureCount()
      _father = [i for i in range(0, featCount)]
      _rank = [0] * featCount
      def _find(x):
        if _father[x] != x:
          _father[x] = _find(_father[x])
        return _father[x]

      def _union(x, y):
        _x = _find(x)
        _y = _find(y)
        if _x == _y:
          return
        if _rank[_x] < _rank[_y]:
          _father[_x] = _y
        elif _rank[_x] > _rank[_y]:
          _father[_y] = _x
        else:
          _father[_y] = _x
          _rank[x] += 1

      for (_, feat_ids) in self.errFeatMap.items():
        for feat_id in feat_ids[1:]:
          _union(feat_id, feat_ids[0])

      feat_set = defaultdict(list)
      for idx, feat in enumerate(_father):
        feat_set[feat].append(idx)

      # Init correct layer
      self.corrLayer =  QgsVectorLayer("LineString?crs=" + self.lineLayer.crs().authid(), 
                                       self.lineLayer.name() + "_correct", "memory")
      corrPr = self.corrLayer.dataProvider()
      self.corrLayer.startEditing()

      # Generate new features
      new_feats = map(self._render_corr_layer, feat_set.values())
      corrPr.addFeatures(new_feats)
      self.corrLayer.commitChanges()
      # # Show the correct layer
      QgsProject.instance().addMapLayer(self.corrLayer)

    def _render_err_layer(self):
      # init err layer and start editing  
      self.errLayer = QgsVectorLayer("Point?crs=" + self.lineLayer.crs().authid(), 
                                     self.lineLayer.name() + "_Pseudo_Point", "memory")
      errPr = self.errLayer.dataProvider()
      self.errLayer.startEditing()
      for (point, feat_ids) in self.errFeatMap.items():
        if len(feat_ids) == 2:
          # Pseudo point
          self.errSet.add(feat_ids[0])
          self.errSet.add(feat_ids[1])
          self.errPointList.extend(map(lambda x: (point, x), feat_ids))

          # Add pseudo point to errLayer
          feat = QgsFeature()
          feat.setGeometry(QgsGeometry.fromPointXY(point))
          errPr.addFeatures([feat])

      for (point, feat_ids) in self.errFeatMap.items():
        if len(feat_ids) != 2:
          for feat_id in feat_ids:
            if feat_id not in self.errSet:
              self.corrSet.add(feat_id)

      self.errLayer.commitChanges()

    def _render_corr_layer(self, feat_ids):
      new_feat = QgsFeature()
      geom = new_feat.geometry()

      # Combine features
      for idx, feat_id in enumerate(feat_ids):
        feat = next(self.lineLayer.getFeatures(QgsFeatureRequest().setFilterFid(feat_id)))
        if idx == 0:
          new_feat.setGeometry(feat.geometry())
          geom = new_feat.geometry()
        else:
          geom = geom.combine(feat.geometry())
      new_feat.setGeometry(geom)
      return new_feat
    
    def _render_table(self):
      for (idx, err) in list(enumerate(self.errPointList)):
        self.model.setItem(idx, 0, QStandardItem(str(err[0].x())))
        self.model.setItem(idx, 1, QStandardItem(str(err[0].y())))
        self.model.setItem(idx, 2, QStandardItem(str(err[1])))
      self.resDlg.mResTableView.setModel(self.model)
      # self.resDlg.mResTableView.selectionModel().currentRowChanged.connect(self.zoom_to_feature)
      w = self.resDlg.mResTableView.width()
      self.resDlg.mResTableView.setColumnWidth(0, w / 3 - 1)
      self.resDlg.mResTableView.setColumnWidth(1, w / 3 - 1)
      self.resDlg.mResTableView.setColumnWidth(2, w - 2 * w / 3 - 2)
    
    def _zoom_to_feature(self, item):
      # Clear previous selection
      for layer in self.canvas.layers():
        if layer.type() == layer.VectorLayer:
          layer.removeSelection()
      self.canvas.refresh()

      # Get id of feature selected
      feat_id = self.model.item(item.row(), 2).data(0)
      self.lineLayer.select(int(feat_id))

      # Zoom canvas
      self.canvas.setExtent(layer.boundingBoxOfSelected())
      self.canvas.refresh()

# class WorkThread(QThread):
#   trigger = pyqtSignal(int)
#   def __init__(self, iface, parent=None):
#     super(WorkThread, self).__init__(parent)
#     self.iface = iface

#   def __del__(self):
#     self.wait()

#   def run(self):
#     lineLayer = self.iface.activeLayer()
#     featCount = lineLayer.featureCount()
#     lineFeatIter = lineLayer.getFeatures()
#     errFeatMap = defaultdict(list)
#     # # map(_map_points, lineFeatIter)
#     print(list(lineFeatIter))
      
#   def _map_points(feat):
#     g = feat.geometry()
    
#     if g.isMultipart():
#       lines = g.asMultiPolyline()
#       for line in lines:
#         startPoint, endPoint = line[0], line[-1]
#         errFeatMap[startPoint] = feat.id()
#         errFeatMap[endPoint] = feat.id()
#     else:
#       line = g.asPolyline()
#       startPoint, endPoint = line[0], line[-1]
#       errFeatMap[startPoint] = feat.id()
#       errFeatMap[endPoint] = feat.id()
